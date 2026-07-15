# OpenUAStudio

OpenUAStudio is the unified asset toolset for **OpenUA / Microsoft Urban Assault (1998)**.
It combines the former 3D asset workbench, BASet extraction and texture conversion workflows, and the former 2D editor in one application.

## Main workbench

The default window provides:

- BASE and SET.BAS family browsing;
- textured SKLT preview with child objects and VANM playback;
- object, polygon, UV and material inspection;
- safe geometry and mapping edits through explicit Save As operations;
- embedded resource preview, Ctrl/Shift multi-selection and extraction;
- double-click preview for embedded SKLT and ILBM/VBMP resources;
- source comparison, dependency resolution and technical reports.

## SET.BAS and texture tools

The BASet workflows are integrated into the SET.BAS tab and Tools menu:

- extract selected resources;
- convert selected embedded VBMP textures directly to usable ILBM;
- non-modal texture previews that leave the maximized workbench untouched;
- extract a complete archive with manifests;
- automatic VBMP to ILBM and PNG conversion;
- optional BASE/KIDS raw developer export;
- optional scene metadata export;
- ILBM/VBMP to PNG conversion;
- VBMP to standalone ILBM conversion;
- template-safe PNG to ILBM conversion;
- open the latest output folder.

The source SET.BAS is always treated as read-only.

## Wireframe Editor

Use **Wireframe Editor** beside the Tools menu to open the complete integrated 2D SKL/SKLT editor. It retains its own editing, outline, save, undo/redo and 3D wireframe-preview functions while sharing the same OpenUAStudio process.

## Supported and researched formats

- SKL / SKLT
- BASE / BAS / SET.BAS
- ILBM / ILB / VBMP
- ANM / VANM
- PNG conversion workflows

## Philosophy

OpenUAStudio favors small, verified changes, original-game compatibility, read-only inspection where possible, and explicit output paths for every write operation.

## License

GNU General Public License v3.0.

## Legal notice

OpenUAStudio is a free, non-commercial community tool for Urban Assault/OpenUA modding, preservation and research. It does not include the full original game content. Users must provide their own legally obtained assets.

Created by TeuZzZ-17. Urban Assault was developed by TerraTools and published by Microsoft in 1998. OpenUAStudio is an independent community project and is not affiliated with Microsoft or TerraTools.
