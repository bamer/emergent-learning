# Visualization Components

## Overview

The visualization components in this directory provide interactive data visualization for the ELF Dashboard.

## Components

### 3D Visualizations

| Component | Description | Min Height | Camera Settings |
|-----------|-------------|------------|-----------------|
| **TreemapView** | Hierarchical data as 3D boxes | `min-h-[500px]` | FOV: 50, Z: 120 |
| **ForceGraph** | Network graph with force simulation | `min-h-[500px]` | FOV: 50, Z: 100 |

### 2D Visualizations

| Component | Description | Min Height |
|-----------|-------------|------------|
| **HeatmapView** | Activity heatmap grid | `min-h-[300px]` |
| **GanttChart** | Timeline/task schedule | `min-h-[300px]` |
| **SankeyDiagram** | Data flow visualization | `min-h-[300px]` |

## Sizing Guidelines

### Minimum Heights
- **3D views**: `min-h-[500px]` - Ensures canvas has enough space for 3D rendering
- **2D views**: `min-h-[300px]` - Compact but readable for grid/table displays

### Header Styling
All visualization headers use:
```jsx
<div className="flex items-center justify-between p-2 border-b border-slate-700">
  <h3 className="text-sm font-semibold text-white">Title</h3>
```

### Container Structure
```jsx
<div className="w-full h-full min-h-[XXXpx] flex flex-col bg-slate-900 rounded-lg">
  {/* Header - flex-shrink-0 implicit */}
  <div className="...">...</div>
  
  {/* Content - flex-1 fills remaining */}
  <div className="flex-1 min-h-0">
    {/* Canvas or content */}
  </div>
</div>
```

## Important Notes

### Do NOT Modify Parent Containers
The parent containers (`DashboardLayout.tsx`, `AdvancedVisualizations.tsx`) control scrolling behavior. Modifying them can break scroll functionality across all tabs.

**Current working parent structure:**
```jsx
// DashboardLayout.tsx - DO NOT CHANGE
<div className="relative z-10 container mx-auto px-4 py-8 pt-24 h-screen max-h-screen overflow-y-auto custom-scrollbar cursor-default pb-24">
    <div className="glass-panel p-6 rounded-xl">
```

### Making Sizing Changes
When adjusting visualization sizes:
1. Modify only the individual component's `min-h-[XXXpx]` value
2. Adjust camera FOV/distance for 3D views
3. Keep header padding at `p-2` for consistency
4. Test in both cosmic and grid view modes

## View Modes

### 3D Mode
- Uses `@react-three/fiber` Canvas
- OrbitControls for pan/zoom/rotate
- Camera position and FOV control initial view

### 2D Mode
- Standard HTML/CSS layout
- Grid or flexbox positioning
- Overflow-auto for scrolling within component
