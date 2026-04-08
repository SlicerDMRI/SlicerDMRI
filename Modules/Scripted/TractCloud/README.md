# TractCloud

Registration-free tractography parcellation using deep learning.

TractCloud classifies individual streamlines from whole-brain tractography
into 42 anatomical white matter tracts using a point cloud neural network
(DGCNN). It operates directly in subject space without requiring registration
to an atlas.

## Usage

**Input:** A FiberBundle node containing whole-brain tractography.

**Output:** A two-level SubjectHierarchy organized by tract category:

```
<InputName>_TractCloud/
    Association/
        arcuate fasciculus (AF)
        cingulum bundle (CB)
        ...
    Projection/
        corticospinal tract (CST)
        ...
    Commissural/
        corpus callosum 1 (CC1)
        ...
    Cerebellar/
        ...
    Superficial/
        ...
    Other/ (optional)
        ...
```

Each tract is assigned a unique solid color from the GenericColors table.

On first use the module automatically downloads pre-trained model weights
(~50 MB) and HCP atlas center data from the
[TractCloud GitHub releases](https://github.com/SlicerDMRI/TractCloud/releases).

### Dependencies

- **tractcloud** pip package -- installed automatically on first use from
  https://github.com/SlicerDMRI/TractCloud
- GPU (CUDA) is used automatically when available

### Testing with the development branch

To test the TractCloud module before the `tractcloud` package is merged
to `main`, install the `inference-cli` branch into Slicer's Python:

```python
# In Slicer's Python console:
slicer.util.pip_install("git+https://github.com/SlicerDMRI/TractCloud.git@inference-cli")
```

Or from the command line:

```bash
PythonSlicer -m pip install "git+https://github.com/SlicerDMRI/TractCloud.git@inference-cli"
```

### Output tracts (42)

| Category | Tracts |
|----------|--------|
| Association (11) | AF, CB, EC, EmC, ILF, IOFF, MdLF, SLF-I, SLF-II, SLF-III, UF |
| Projection (11) | CST, CR-F, CR-P, SF, SO, SP, TF, TO, TT, TP, PLIC |
| Commissural (7) | CC1--CC7 |
| Cerebellar (5) | CPC, ICP, Intra-CBLM-I-P, Intra-CBLM-PaT, MCP |
| Superficial (8) | Sup-F, Sup-FP, Sup-O, Sup-OT, Sup-P, Sup-PO, Sup-PT, Sup-T |

An optional "Other" category collects streamlines not assigned to any
anatomical tract.

## Source repositories

- **TractCloud model and training code:**
  https://github.com/SlicerDMRI/TractCloud
- **SlicerDMRI extension:**
  https://github.com/SlicerDMRI/SlicerDMRI
- **ORG white matter atlas:**
  http://dmri.slicer.org/atlases/

## References

If you use this module, please cite the following papers:

> Tengfei Xue, Yuqian Chen, Chaoyi Zhang, Alexandra J. Golby,
> Nikos Makris, Yogesh Rathi, Weidong Cai, Fan Zhang,
> Lauren J. O'Donnell.
> **TractCloud: Registration-free tractography parcellation with a novel
> local-global streamline point cloud representation.**
> *International Conference on Medical Image Computing and Computer
> Assisted Intervention (MICCAI)*, 2023.

> Fan Zhang, Ye Wu, Ian Norton, Yogesh Rathi, Nikos Makris,
> Lauren J. O'Donnell.
> **An anatomically curated fiber clustering white matter atlas for
> consistent white matter tract parcellation across the lifespan.**
> *NeuroImage*, 179:429-447, 2018.

## License

Released under the [Slicer License](https://github.com/SlicerDMRI/TractCloud/blob/main/LICENSE).
