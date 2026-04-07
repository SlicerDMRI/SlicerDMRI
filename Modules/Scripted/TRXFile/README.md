# TRXFile Module

Reader and writer for the [TRX tractography file format](https://github.com/tee-ar-ex/trx-spec)
using the [trx-python](https://github.com/tee-ar-ex/trx-python) package.
Also loads VTK legacy files that contain fiber bundle polylines.

## TRX to MRML Mapping

### Coordinate System

Both TRX and Slicer fiber bundles use **RAS** (Right-Anterior-Superior)
world coordinates in millimeters.  TRX calls this RASMM.  No coordinate
conversion is performed during read or write.

### Core Data

| TRX concept | MRML representation |
|---|---|
| `positions` (NB_VERTICES x 3) | `vtkPoints` on the FiberBundleNode's polydata |
| `offsets` / streamline connectivity | `vtkCellArray` lines on the polydata |
| `data_per_vertex` arrays | Point data arrays on the polydata (`vtkPointData`) |
| `data_per_streamline` arrays | Cell data arrays on the polydata (`vtkCellData`) |

### Header

The TRX header fields `VOXEL_TO_RASMM` (4x4 affine) and `DIMENSIONS`
(3-element grid size) are stored as a JSON string in the MRML node
attribute `TRX.Header`.  This preserves them for round-trip fidelity.
When writing a FiberBundleNode that has no `TRX.Header` attribute, the
writer uses an identity affine and `[1, 1, 1]` dimensions.

### Groups

TRX groups are named subsets of streamline indices that can overlap.
Each group becomes a separate `vtkMRMLFiberBundleNode` organized under a
`SubjectHierarchy` folder:

```
SubjectHierarchy folder "<baseName>"
  +-- <baseName>_all     (complete tractogram, TRX.Role = "all")
  +-- <groupName_1>      (subset, TRX.Role = "group")
  +-- <groupName_2>      (subset, TRX.Role = "group")
  ...
```

If the TRX file has no groups, a single FiberBundleNode is created
without a folder.

The `_all` node contains the full streamline set with all
`data_per_vertex` and `data_per_streamline` arrays.  Group nodes contain
only their subset of streamlines and associated per-vertex/per-streamline
data.

When writing back to TRX, group membership is reconstructed by matching
streamlines between group nodes and the `_all` node using first and last
point coordinates.

### Per-Group Data

TRX `data_per_group` (metadata attached to groups, such as mean FA or
volume) is stored as MRML node attributes on each group's
FiberBundleNode with the prefix `TRX.dpg.`:

| TRX | MRML node attribute |
|---|---|
| `data_per_group["AF_L"]["mean_fa"]` | `TRX.dpg.mean_fa` on the AF_L node |

The same values are also stored on the SubjectHierarchy folder item with
the key `TRX.dpg.<groupName>.<attrName>`.

### VTK Fiber Loading

The reader also accepts `.vtk` files.  A lightweight header scan
(without reading geometry) checks for the `LINES` keyword and absence of
`POLYGONS` to distinguish fiber bundles from surface meshes.  Confirmed
fiber files are loaded directly via `vtkPolyDataReader` into a
FiberBundleNode with all point and cell data arrays preserved.

## Self-Test

The module includes a self-test (`TRXFileTest`) that:

1. Downloads the [gold standard test data](https://github.com/tee-ar-ex/trx-test-data)
   (`gs.trx`) via the `trx.fetcher` API.
2. Loads it and verifies streamline/vertex counts, coordinate accuracy,
   and preservation of `data_per_vertex` and `data_per_streamline` arrays.
3. Writes the fiber bundle back to TRX and reloads it, checking that
   streamline counts, coordinates (within float16 tolerance), data array
   keys, and the header affine all survive the round trip.
