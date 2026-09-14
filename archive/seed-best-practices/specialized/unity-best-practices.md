# Unity Best Practices

**Purpose**: Unity development standards, scene architecture, singleton patterns, and event naming.
**Status**: 🟢 Active
**Tags**: #architecture, #unity, #standards

## Overview
This document captures Unity development best practices for the Sudoku App project. Follow these guidelines to ensure consistent, performant, and maintainable code.

**Code Location**: `Scripts/Core/GameLogger.cs`

---

## Quick Reference

| # | Rule | Summary |
|---|---|---|
| [1](#namespace-strategy) | **Namespaces** | Global namespace for this project size (<100 classes). |
| [2](#scene-architecture-bootstrap-pattern) | **Bootstrap** | `BootstrapScene` (Index 0) initializes persistent managers. |
| [3](#singleton-manager-pattern) | **Singletons** | Use `Instance` + `DontDestroyOnLoad`. No duplicates. |
| [4](#editor-factories) | **Factories** | Use Editor scripts to create consistent UI elements. |
| [5](#ui-text) | **UI Text** | Always use **TextMeshPro**. Legacy Text is fallback only. |
| [6](#centering-ui-elements) | **Layouts** | specific anchor/pivot settings for responsive UI. |
| [7](#event-naming-conventions) | **Events** | `FireEventName` (outgoing) / `HandleEventName` (incoming). |
| [8](#asset-loading-for-runtime-sprites) | **Asset Loading** | `Resources.Load<Sprite>()` for runtime. NEVER `AssetDatabase` outside Editor. |

---

## Namespace Strategy

**For this small project (< 100 classes, single developer), we use GLOBAL NAMESPACES.**

### Decision Framework
- ✅ **Use Namespaces When:**
  - Codebase > 100 classes
  - Multiple teams/developers
  - Creating reusable libraries/packages
  - Professional asset development
  - Need clear API boundaries

- ❌ **Skip Namespaces When:**
  - < 50 classes, single developer
  - Rapid prototyping/iteration
  - Simple game logic
  - Learning/experimental projects

### Rationale
- **Development Speed**: Global namespace reduces friction during rapid development
- **Unity Conventions**: Most Unity tutorials and small projects use global namespace
- **YAGNI Principle**: Don't add complexity we don't currently need
- **Easy Refactoring**: Can add namespaces later if project grows

### Current Implementation
- All classes in global namespace (including managers)
- No `using` directives needed between classes
- Consistent with Unity's default script templates

---

## Scene Architecture (Bootstrap Pattern)

### Overview
Use a **Bootstrap Scene** to initialize all persistent managers before loading any game scenes. This ensures managers are available across all scenes without duplicates.

### Build Settings Order
```
0. BootstrapScene     ← Loads first, creates persistent objects
1. SplashScene
2. GameScene
3. SettingsScene
4. DebugMenuScene
5. DebugCellScene
6. DebugBoardScene
```

### What Goes Where

| Element | Location | Persists? | Reason |
|---------|----------|-----------|--------|
| **Camera** | Per-scene | ❌ No | Each scene configures its own camera |
| **EventSystem** | BootstrapScene | ✅ Yes | Only ONE allowed - multiple causes issues |
| **ThemeManager** | BootstrapScene | ✅ Yes | Theme survives scene changes |
| **SoundManager** | BootstrapScene | ✅ Yes | Music/SFX continues across scenes |
| **GameManager** | BootstrapScene | ✅ Yes | Central game state |
| **Canvas + UI** | Per-scene | ❌ No | Each screen has its own UI |

### Flow Diagram
```
App Starts
    │
    ▼
BootstrapScene Loads (index 0)
    │
    ├── Creates EventSystem (DontDestroyOnLoad)
    ├── Creates ThemeManager (DontDestroyOnLoad)
    ├── Creates SoundManager (DontDestroyOnLoad)
    └── BootstrapManager loads SplashScene
    │
    ▼
SplashScene Loads
    ├── Has its own Camera
    ├── Has its own Canvas + UI
    └── Uses persistent managers from Bootstrap
```

### Key Rules
1. **BootstrapScene is ALWAYS index 0** in Build Settings
2. **Never put EventSystem in game scenes** - it comes from Bootstrap
3. **Never put managers in game scenes** - they come from Bootstrap
4. **Each game scene has:** Camera, Canvas, scene-specific scripts

---

## Singleton Manager Pattern

### Standard Template

```csharp
public class MyManager : MonoBehaviour
{
    public static MyManager Instance { get; private set; }

    private void Awake()
    {
        if (Instance == null)
        {
            Instance = this;
            DontDestroyOnLoad(gameObject);
            Initialize(); // Optional setup
        }
        else
        {
            Destroy(gameObject); // Duplicate - destroy it
        }
    }

    private void Initialize()
    {
        // One-time setup here
    }
}
```

### Usage in Other Scripts
```csharp
// Access the singleton
ThemeManager.Instance.SetTheme(newTheme);
SoundManager.Instance.PlaySFX(clipName);
```

### Important Notes
- ✅ Always check `if (Instance == null)` before assigning
- ✅ Always call `DontDestroyOnLoad(gameObject)`
- ✅ Always `Destroy(gameObject)` if duplicate
- ❌ Never put singleton managers in multiple scenes

---

## Editor Factories

### Purpose
Editor Factories are **Editor-only scripts** that create and configure UI elements via Unity's menu system. They ensure consistency and prevent manual setup errors.

### Location
All Editor scripts go in: `Assets/Editor/`

### Available Factories

#### UIEditorFactory
Creates standard UI elements with correct settings.

| Menu Path | Creates |
|-----------|---------|
| `GameObject/UI/Sudoku/Canvas (Standard)` | Canvas with proper Canvas Scaler settings |
| `GameObject/UI/Sudoku/Button Panel` | Vertical layout container for buttons |
| `GameObject/UI/Sudoku/Menu Button` | Button with Layout Element for use in panels |
| `GameObject/UI/Sudoku/Corner Button` | Icon button anchored to a corner |
| `GameObject/UI/Sudoku/Title Text` | Centered TMP text for titles |
| `GameObject/UI/Sudoku/Back Button` | Standard back navigation button |

### How to Use
1. In Unity Editor, go to **GameObject → UI → Sudoku**
2. Select the element type you need
3. Element is created with all correct settings applied

### Benefits
- ✅ Consistent settings every time
- ✅ No manual configuration errors
- ✅ Faster scene setup
- ✅ Changes to factory update all future elements

### Creating New Factories
```csharp
// In Assets/Editor/UIEditorFactory.cs
using UnityEditor;
using UnityEngine;

public static class UIEditorFactory
{
    [MenuItem("GameObject/UI/Sudoku/My Element", false, 10)]
    public static void CreateMyElement()
    {
        // Create and configure the element
    }
}
```

---

## RectTransform Field Behavior

Understanding when you see different fields in the Inspector:

| Anchor Setup | Fields Shown | Use Case |
|--------------|--------------|----------|
| **Same Min/Max** (e.g., both 0.5, 0.5) | `Pos X`, `Pos Y`, `Width`, `Height` | Fixed-size elements positioned relative to a point |
| **Different Min/Max** (e.g., 0,0 to 1,1) | `Left`, `Right`, `Top`, `Bottom` | Elements that stretch to fill parent |
| **Mixed** (e.g., X: 0→1, Y: 0.5→0.5) | `Left`, `Right`, `Pos Y`, `Height` | Horizontal stretch, vertical fixed |

---

## UI Text

### Always Use TextMeshPro
- **Preferred**: `TextMeshPro - UI` (GameObject → UI → Text - TextMeshPro)
- **Fallback**: Legacy `UI Text` (only if TMP not available)

### Why TextMeshPro?
- Better visual quality (crisper text at all scales)
- Significantly better performance (reduced draw calls)
- Uses SDF (Signed Distance Field) fonts with texture atlases
- Advanced text styling options
- Better control over character spacing
- Robust layout options

---

## Centering UI Elements

### Best Practice: Stretch Anchors + Text Alignment

For centering text on screen (especially for mobile with varying screen sizes):

#### RectTransform Settings
| Property | Value | Notes |
|----------|-------|-------|
| Anchor Min | (0, 0) | Bottom-left |
| Anchor Max | (1, 1) | Top-right (stretch to fill) |
| Left | 0 | Or add padding (e.g., 50) |
| Right | 0 | Or add padding (e.g., 50) |
| Top | 0 | Or add padding (e.g., 50) |
| Bottom | 0 | Or add padding (e.g., 50) |
| Pivot | (0.5, 0.5) | Center |

#### Text Component Settings
| Property | Value |
|----------|-------|
| Alignment | **Middle Center** |
| Horizontal Overflow | Wrap or Overflow |
| Vertical Overflow | Overflow |

### Why This Approach?
- ✅ **Responsive**: Automatically adapts to any screen size/aspect ratio
- ✅ **Works with Canvas Scaler**: Properly scales across all devices
- ✅ **Simple setup**: No guessing pixel dimensions
- ✅ **Mobile-safe**: Works on phones, tablets, different aspect ratios

### Avoid: Fixed Width/Height with Center Anchors
- ❌ Not responsive to different screen sizes
- ❌ Text may overflow or appear tiny on different devices
- ❌ Requires manual adjustment for each target resolution

---

## Button Groups (Vertical Layout)

For a group of buttons (e.g., menu buttons), use a **Vertical Layout Group** with a parent container.

### Parent Container Setup (e.g., "ButtonPanel")

| Property | Value | Notes |
|----------|-------|-------|
| **Anchor Preset** | Middle-Center | Click the center square in anchor grid |
| Anchor Min | (0.5, 0.5) | Same value = fixed position |
| Anchor Max | (0.5, 0.5) | Same value = fixed position |
| Pivot | (0.5, 0.5) | Center |
| Pos X | `0` | Horizontally centered |
| Pos Y | Adjust as needed | Negative = below center |
| Width | `400` (or desired) | Panel width |

**Add Components:**

1. **Vertical Layout Group:**

| Property | Value |
|----------|-------|
| Spacing | `20` |
| Child Alignment | `Middle Center` |
| Control Child Size - Width | ✅ |
| Control Child Size - Height | ❌ |
| Child Force Expand - Width | ✅ |
| Child Force Expand - Height | ❌ |

2. **Content Size Fitter:**

| Property | Value |
|----------|-------|
| Horizontal Fit | `Unconstrained` |
| Vertical Fit | `Preferred Size` |

### Individual Button Setup (children of container)

Each button needs a **Layout Element** component:

| Property | Value |
|----------|-------|
| Preferred Height | `80` (or desired) |

The Layout Group handles width and positioning automatically.

### Code Support

Use `ButtonFactory.ConfigureButtonInLayoutGroup()` to apply standard settings:

```csharp
// In editor or runtime setup
ButtonFactory.ConfigureButtonInLayoutGroup(myButton, preferredHeight: 80);
```

---

## Corner-Anchored Elements (Settings Gear, etc.)

For icons/buttons anchored to a corner:

| Property | Value (Top-Right example) |
|----------|---------------------------|
| Anchor Preset | Top-Right corner |
| Anchor Min | (1, 1) |
| Anchor Max | (1, 1) |
| Pivot | (1, 1) - same corner |
| Pos X | `-30` (padding from edge) |
| Pos Y | `-30` (padding from edge) |
| Width | `60` (fixed) |
| Height | `60` (fixed) |

**Corner Pivot Reference:**
- Top-Left: Pivot (0, 1)
- Top-Right: Pivot (1, 1)
- Bottom-Left: Pivot (0, 0)
- Bottom-Right: Pivot (1, 0)

---

## Canvas Scaler Configuration

For mobile games, always configure the Canvas Scaler:

| Property | Value | Notes |
|----------|-------|-------|
| UI Scale Mode | `Scale With Screen Size` | Required for responsiveness |
| Reference Resolution | `1080 x 1920` | Portrait mobile standard |
| Screen Match Mode | `Match Width Or Height` | |
| Match | `0.5` to `1` | 0.5 = balanced, 1 = match height (good for portrait) |

---

## Event Naming Conventions

### Fire + Handle Pattern

Use consistent naming for event declaration and handling:

**Event Declaration (Outgoing):**
```csharp
public event Action<T> FireEventName;  // Fires/invokes the event
```

**Event Handler (Incoming):**
```csharp
private void HandleEventName(T parameter)  // Handles/receives the event
{
    // Process the event
}
```

### Examples

```csharp
// Component A (sender)
public event Action<int> FireValueChanged;
private void OnValueChanged(int newValue)
{
    FireValueChanged?.Invoke(newValue);
}

// Component B (receiver)
private void Start()
{
    componentA.FireValueChanged += HandleValueChanged;
}

private void HandleValueChanged(int newValue)
{
    // Process the value change
    UpdateUI(newValue);
}
```

### Naming Rules

| Event Type | Prefix | Example |
|------------|--------|---------|
| **Outgoing Events** | `Fire` | `FireCellSelected`, `FireBoardChanged`, `FireControlPadPressed` |
| **Incoming Handlers** | `Handle` | `HandleCellSelected`, `HandleBoardChanged`, `HandleControlPadPressed` |

### Why This Pattern?

- **Clear Intent**: `Fire` = sends, `Handle` = receives
- **Consistent**: Easy to find related code by searching prefixes
- **Self-Documenting**: Method names clearly indicate event flow direction
- **Debugging**: Easy to trace event chains in logs

### Common Event Flows

```
ComponentA.FireSomething → ComponentB.HandleSomething
SudokuBoardView.FireCellSelected → GameManager.HandleCellSelected
ControlPad.FireControlPadPressed → GameManager.HandleControlPadPressed
```

---

## Asset Loading for Runtime Sprites

### Rule: Use `Resources.Load<Sprite>()` for Runtime-Loaded Sprites

**This is THE standard for loading sprites at runtime in this project.**

Any sprite that needs to be loaded dynamically (not wired via `[SerializeField]` in Inspector) MUST be placed in a `Resources/` folder and loaded via `Resources.Load<Sprite>()`.

### ⚠️ NEVER Use `AssetDatabase` for Runtime Code

`AssetDatabase` is **editor-only** — it does NOT exist in device builds. Code using it will compile with `#if UNITY_EDITOR` but returns `null` on iOS/Android.

### ❌ BAD - Editor-Only API

```csharp
#if UNITY_EDITOR
    return AssetDatabase.LoadAssetAtPath<Sprite>(path);
#else
    return null;  // ALL sprites are null on device!
#endif
```

### ✅ GOOD - Resources.Load (Works Everywhere)

```csharp
// Path is relative to ANY Resources/ folder, NO file extension
return Resources.Load<Sprite>("Sprites/Icons/NotoEmoji/back-1-100px");
```

### Resources.Load Path Rules

| Rule | Example |
|------|---------|
| Path is relative to `Resources/` folder | `"Sprites/Icons/NotoEmoji/back-1-100px"` |
| Do NOT include `Assets/Resources/` prefix | ❌ `"Assets/Resources/Sprites/Icons/..."` |
| Do NOT include file extension | ❌ `"Sprites/Icons/.../back-1-100px.png"` |
| Use forward slashes | ✅ `"Sprites/Icons/NotoEmoji"` |

### Current Resources/ Structure

```
Assets/Resources/
├── Puzzles/              # Puzzle JSON data
├── PuzzleLists/          # Puzzle list metadata
└── Sprites/Icons/        # Icon packs (runtime-loaded)
    ├── NotoEmoji/         # 11 icons per pack
    ├── IconParkColor/
    ├── Heroicons/
    ├── Tabler/
    ├── Twemoji/
    ├── FluentEmojiColor/
    ├── Lucide/
    ├── Material/
    ├── gear-4-120px.png   # Settings gear icon
    └── undo-1-120px.png   # Undo/reset icon
```

### When to Use Each Loading Pattern

| Pattern | When to Use |
|---------|-------------|
| `[SerializeField]` | Static sprites wired in Inspector (buttons, backgrounds) |
| `Resources.Load<Sprite>()` | Dynamic sprites loaded by name at runtime (icon packs, switchable content) |
| `AssetDatabase.LoadAssetAtPath` | **Editor scripts ONLY** (factories in `Assets/Editor/`) |

### Why Not Addressables?

For this project size (~88 icon sprites, ~2-3 MB total), `Resources.Load` is the right choice:
- Zero additional packages or build steps
- Synchronous loading = instant icon pack switching
- Matches existing pattern (puzzle JSON loading)
- Future upgrade: can add SpriteAtlases on top if draw calls become an issue

---

## Performance Tips

### UI Text Performance
- Avoid excessive use of `Best Fit` (CPU-intensive)
- Use TextMeshPro for better batching and fewer draw calls
- Minimize dynamic text updates when possible

### UI Rebuilds
- Avoid frequently modifying RectTransform properties
- Group static UI elements together
- Use Canvas Groups for visibility toggling instead of SetActive

---

## Quick Reference

### Bootstrap Scene Checklist
1. ☐ BootstrapScene is index 0 in Build Settings
2. ☐ BootstrapScene contains: EventSystem, ThemeManager, BootstrapManager
3. ☐ All managers use singleton pattern with DontDestroyOnLoad
4. ☐ Game scenes do NOT have EventSystem
5. ☐ Game scenes do NOT have manager duplicates
6. ☐ Game scenes have their own Camera and Canvas

### Centering Text Checklist
1. ☐ Use TextMeshPro (not legacy Text)
2. ☐ Set anchors to Stretch (Min 0,0 / Max 1,1)
3. ☐ Set Left/Right/Top/Bottom to 0 (or padding value)
4. ☐ Set Pivot to (0.5, 0.5)
5. ☐ Set Text Alignment to Middle Center
6. ☐ Verify Canvas Scaler is set to "Scale With Screen Size"

### New Scene Checklist
1. ☐ Create scene via File → New Scene → Basic (Built-in)
2. ☐ Add Camera (if not present)
3. ☐ Do NOT add EventSystem (comes from Bootstrap)
4. ☐ Do NOT add ThemeManager (comes from Bootstrap)
5. ☐ Use Editor Factory to create Canvas: GameObject → UI → Sudoku → Canvas (Standard)
6. ☐ Add scene-specific UI and scripts
7. ☐ Add scene to Build Settings

---

**Created**: December 5, 2025
**Updated**: February 20, 2026 — Added Rule 8 (Asset Loading for Runtime Sprites)
**Source**: Exa-ai code search + Second Opinion MCP analysis
