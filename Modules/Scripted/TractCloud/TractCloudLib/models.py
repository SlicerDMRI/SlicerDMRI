"""TractCloud neural network models (DGCNN and PointNet).

Adapted from https://github.com/SlicerDMRI/TractCloud
Original authors: Tengfei Xue et al.
Reference: TractCloud: Registration-free tractography parcellation with a novel
local-global streamline point cloud representation (MICCAI 2023).
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


# ---------------------------------------------------------------------------
# DGCNN helpers
# ---------------------------------------------------------------------------

def tract_knn(x, k):
    """Point-level k-nearest neighbors within each streamline.

    Args:
        x: (N_fiber, num_dims, N_point)
        k: number of neighbor points per point
    Returns:
        idx: (N_fiber, N_point, k)
    """
    inner = -2 * torch.matmul(x.transpose(2, 1), x)
    xx = torch.sum(x ** 2, dim=1, keepdim=True)
    pairwise_distance = -xx - inner - xx.transpose(2, 1)
    idx = pairwise_distance.topk(k=k, dim=-1)[1]
    return idx


def get_tract_graph_feature(x, k_point_level=15, device=torch.device("cpu")):
    """Build edge features for points on individual streamlines.

    Args:
        x: (N_fiber, num_dims, N_point)
        k_point_level: number of neighbor points per point
        device: torch device
    Returns:
        feature: (N_fiber, 2*num_dims, N_point, k)
    """
    num_fibers = x.size(0)
    num_dims = x.size(1)
    num_points = x.size(2)

    if k_point_level >= num_points:
        idx = (torch.arange(0, num_points)[None, None, :]
               .repeat(num_fibers, num_points, 1).to(device))
    else:
        idx = tract_knn(x, k=k_point_level)

    idx_base = (torch.arange(0, num_fibers, device=device)
                .view(-1, 1, 1) * num_points)
    idx = (idx + idx_base).view(-1)

    x = x.transpose(2, 1).contiguous()
    feature = x.view(num_fibers * num_points, -1)[idx, :]
    feature = feature.view(num_fibers, num_points, k_point_level, num_dims)
    x = x.view(num_fibers, num_points, 1, num_dims).repeat(1, 1, k_point_level, 1)

    feature = torch.cat((feature - x, x), dim=3).permute(0, 3, 1, 2).contiguous()
    return feature


# ---------------------------------------------------------------------------
# DGCNN classifier
# ---------------------------------------------------------------------------

class TractDGCNN(nn.Module):
    """Dynamic Graph CNN for streamline classification."""

    def __init__(self, num_classes, k=20, k_global=80, k_point_level=5,
                 emb_dims=1024, dropout=0.5, device=torch.device("cpu")):
        super().__init__()
        self.fiber_level_k = k
        self.fiber_level_k_global = k_global
        self.k_point_level = k_point_level
        self.device = device

        self.bn1 = nn.BatchNorm2d(64)
        self.bn2 = nn.BatchNorm2d(64)
        self.bn3 = nn.BatchNorm2d(128)
        self.bn4 = nn.BatchNorm2d(256)
        self.bn5 = nn.BatchNorm1d(emb_dims)

        self.conv1 = nn.Sequential(
            nn.Conv2d(6, 64, kernel_size=1, bias=False), self.bn1,
            nn.LeakyReLU(negative_slope=0.2))
        self.conv2 = nn.Sequential(
            nn.Conv2d(128, 64, kernel_size=1, bias=False), self.bn2,
            nn.LeakyReLU(negative_slope=0.2))
        self.conv3 = nn.Sequential(
            nn.Conv2d(128, 128, kernel_size=1, bias=False), self.bn3,
            nn.LeakyReLU(negative_slope=0.2))
        self.conv4 = nn.Sequential(
            nn.Conv2d(256, 256, kernel_size=1, bias=False), self.bn4,
            nn.LeakyReLU(negative_slope=0.2))
        self.conv5 = nn.Sequential(
            nn.Conv1d(512, emb_dims, kernel_size=1, bias=False), self.bn5,
            nn.LeakyReLU(negative_slope=0.2))

        self.linear1 = nn.Linear(emb_dims * 2, 512, bias=False)
        self.bn6 = nn.BatchNorm1d(512)
        self.dp1 = nn.Dropout(p=dropout)
        self.linear2 = nn.Linear(512, 256)
        self.bn7 = nn.BatchNorm1d(256)
        self.dp2 = nn.Dropout(p=dropout)
        self.linear3 = nn.Linear(256, num_classes)

    def forward(self, x, info_point_set):
        """Forward pass.

        Args:
            x: (B, 3, N_point) streamline coordinates
            info_point_set: (B, 3, N_point, k+k_global) local+global context
        Returns:
            log-softmax predictions (B, num_classes)
        """
        num_fiber = x.size(0)
        if self.fiber_level_k + self.fiber_level_k_global == 0:
            x = get_tract_graph_feature(x, k_point_level=self.k_point_level,
                                        device=self.device)
        else:
            x = x[:, :, :, None].repeat(
                1, 1, 1, self.fiber_level_k + self.fiber_level_k_global)
            x = torch.cat((info_point_set - x, x), dim=1)

        x = self.conv1(x)
        x1 = x.max(dim=-1, keepdim=False)[0]

        x = get_tract_graph_feature(x1, k_point_level=self.k_point_level,
                                    device=self.device)
        x = self.conv2(x)
        x2 = x.max(dim=-1, keepdim=False)[0]

        x = get_tract_graph_feature(x2, k_point_level=self.k_point_level,
                                    device=self.device)
        x = self.conv3(x)
        x3 = x.max(dim=-1, keepdim=False)[0]

        x = get_tract_graph_feature(x3, k_point_level=self.k_point_level,
                                    device=self.device)
        x = self.conv4(x)
        x4 = x.max(dim=-1, keepdim=False)[0]

        x = torch.cat((x1, x2, x3, x4), dim=1)
        x = self.conv5(x)
        x1 = F.adaptive_max_pool1d(x, 1).view(num_fiber, -1)
        x2 = F.adaptive_avg_pool1d(x, 1).view(num_fiber, -1)
        x = torch.cat((x1, x2), 1)

        x = F.leaky_relu(self.bn6(self.linear1(x)), negative_slope=0.2)
        x = self.dp1(x)
        x = F.leaky_relu(self.bn7(self.linear2(x)), negative_slope=0.2)
        x = self.dp2(x)
        x = self.linear3(x)
        return F.log_softmax(x, dim=1)


# ---------------------------------------------------------------------------
# PointNet helpers
# ---------------------------------------------------------------------------

class STN3d(nn.Module):
    """Spatial transformer network for 3D points."""

    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv1d(3, 64, 1)
        self.conv2 = nn.Conv1d(64, 128, 1)
        self.conv3 = nn.Conv1d(128, 1024, 1)
        self.fc1 = nn.Linear(1024, 512)
        self.fc2 = nn.Linear(512, 256)
        self.fc3 = nn.Linear(256, 9)
        self.bn1 = nn.BatchNorm1d(64)
        self.bn2 = nn.BatchNorm1d(128)
        self.bn3 = nn.BatchNorm1d(1024)
        self.bn4 = nn.BatchNorm1d(512)
        self.bn5 = nn.BatchNorm1d(256)

    def forward(self, x):
        batchsize = x.size(0)
        x = F.relu(self.bn1(self.conv1(x)))
        x = F.relu(self.bn2(self.conv2(x)))
        x = F.relu(self.bn3(self.conv3(x)))
        x = torch.max(x, 2, keepdim=True)[0].view(-1, 1024)
        x = F.relu(self.bn4(self.fc1(x)))
        x = F.relu(self.bn5(self.fc2(x)))
        x = self.fc3(x)
        iden = (torch.eye(3, dtype=x.dtype, device=x.device)
                .view(1, 9).repeat(batchsize, 1))
        return (x + iden).view(-1, 3, 3)


class PointNetFeat(nn.Module):
    """PointNet feature extractor."""

    def __init__(self, global_feat=True, feature_transform=False):
        super().__init__()
        self.stn = STN3d()
        self.conv1 = nn.Conv1d(3, 64, 1)
        self.conv2 = nn.Conv1d(64, 128, 1)
        self.conv3 = nn.Conv1d(128, 1024, 1)
        self.bn1 = nn.BatchNorm1d(64)
        self.bn2 = nn.BatchNorm1d(128)
        self.bn3 = nn.BatchNorm1d(1024)
        self.global_feat = global_feat
        self.feature_transform = feature_transform

    def forward(self, x):
        n_pts = x.size(2)
        trans = self.stn(x)
        x = x.transpose(2, 1)
        x = torch.bmm(x, trans)
        x = x.transpose(2, 1)
        x = F.relu(self.bn1(self.conv1(x)))
        pointfeat = x
        x = F.relu(self.bn2(self.conv2(x)))
        x = self.bn3(self.conv3(x))
        x = torch.max(x, 2, keepdim=True)[0].view(-1, 1024)
        if self.global_feat:
            return x, trans, None
        x = x.view(-1, 1024, 1).repeat(1, 1, n_pts)
        return torch.cat([x, pointfeat], 1), trans, None


class PointNetCls(nn.Module):
    """PointNet classifier for streamlines."""

    def __init__(self, k=20, k_global=80, num_classes=1600,
                 feature_transform=False, first_feature_transform=False):
        super().__init__()
        self.k = k
        self.k_global = k_global
        self.feature_transform = feature_transform
        self.feat = PointNetFeat(global_feat=True,
                                 feature_transform=feature_transform)
        self.fc1 = nn.Linear(1024, 512)
        self.fc2 = nn.Linear(512, 256)
        self.fc3 = nn.Linear(256, num_classes)
        self.dropout = nn.Dropout(p=0.3)
        self.bn1 = nn.BatchNorm1d(512)
        self.bn2 = nn.BatchNorm1d(256)

    def forward(self, x, info_point_set):
        x, trans, trans_feat = self.feat(x)
        x = F.relu(self.bn1(self.fc1(x)))
        x = F.relu(self.bn2(self.dropout(self.fc2(x))))
        x = self.fc3(x)
        return F.log_softmax(x, dim=1), trans, trans_feat
