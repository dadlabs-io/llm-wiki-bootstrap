# UI Best Practices

**Purpose**: Consistent patterns for UI development, including localization, factories, and event wiring.
**Status**: 🟢 Active
**Tags**: #architecture, #ui, #standards

## Overview

This document defines consistent patterns for UI development in Unity projects. Following these patterns ensures:
- Consistent appearance across all screens
- Proper localization and runtime text replacement
- Clean separation of designer and runtime responsibilities
- Easy maintenance and refactoring

---

## Quick Reference

| # | Rule | Summary |
|---|---|---|
| [1](#1-designer-vs-runtime-text-pattern) | **Text Pattern** | Designer = ALL CAPS placeholder. Runtime = Localized. |
| [2](#2-serializefield-inspector-reference-pattern) | **References** | Use `[SerializeField]` to wire UI in Inspector. |
| [3](#3-setupui-pattern) | **SetupUI** | Call `SetupUI()` in `Start()` for localization. |
| [4](#4-button-event-wiring-pattern) | **Event Wiring** | Wire listeners in Script (`SetupButtons`), not Factory. |
| [5](#5-factory-pattern-standards) | **Factories** | Create UI hierarchy/style in Editor Factory. |
| [6](#6-theme-color-application) | **Themes** | Apply colors via `ThemeManager`, no hardcoding. |
| [7](#9-localization-process-complete-workflow) | **Localization** | Key → LanguageData → UI call. |

---

## 1. Designer vs Runtime Text Pattern

### Rule: Use placeholders in Editor, real text at Runtime

**Designer Responsibility (Unity Editor):**
- Set text to **ALL CAPS PLACEHOLDER** describing the content.
- Example: "SCORE: 0000", "LEVEL 1", "START GAME".
- This makes it obvious which text is dynamic and waiting for localization.

**Runtime Responsibility (Code):**
- `SetupUI()` replaces the placeholder with the localized string.

### Why?
- Prevents "missing localization" bugs (if you see ALL CAPS in game, you missed a spot).
- Allows designers to layout with worst-case string lengths.

---

## 2. SerializeField Inspector Reference Pattern

### Rule: Wire UI components in the Inspector

Don't use `GameObject.Find` or `transform.Find` for UI elements. It's brittle and slow.

**Do This:**
```csharp
[Header("UI Components")]
[SerializeField] private TextMeshProUGUI titleText;
[SerializeField] private Button startButton;
```

**Don't Do This:**
```csharp
private void Start() {
    titleText = transform.Find("Title").GetComponent<TextMeshProUGUI>(); // ❌ Brittle
}
```

---

## 3. SetupUI Pattern

### Rule: Centralize initialization

Every View component should have a `SetupUI()` method called in `Start()`.

```csharp
private void Start()
{
    SetupUI();
    SetupButtons();
}

private void SetupUI()
{
    // Localize static text
    titleText.text = LocalizedStrings.Get("main_menu_title");
    
    // Apply theme
    background.color = ThemeManager.GetColor("background_primary");
}
```

---

## 4. Button Event Wiring Pattern

### Rule: Wire listeners in code, not Inspector

Inspector events (`On Click()`) are hard to debug and break easily when renaming methods.

**Do This:**
```csharp
private void SetupButtons()
{
    startButton.onClick.AddListener(OnStartClicked);
    settingsButton.onClick.AddListener(OnSettingsClicked);
}

private void OnStartClicked()
{
    GameManager.Instance.StartGame();
}
```

---

## 5. Factory Pattern Standards

### Rule: Use Editor Factories for complex UI creation

For lists, grids, or complex hierarchies, write a static `EditorFactory` method to generate them in the Scene view. This ensures consistent structure.

*(See `unity-best-practices.md` for Editor Scripting details)*

---

## 6. Theme Color Application

### Rule: No hardcoded colors in Inspector

All UI colors must come from the `ThemeManager`.

```csharp
// In SetupUI()
panelImage.color = ThemeManager.GetColor("panel_background");
titleText.color = ThemeManager.GetColor("text_primary");
```

---

## 7. Localization Process (Complete Workflow)

1. **Add Key**: Add generic key to `LocalizedStrings.cs` (e.g., `const string KEY_GAME_OVER = "game_over";`).
2. **Add Data**: Add translation to `Resources/Languages/en.json`.
3. **Wire UI**: In `SetupUI()`, set `textComponent.text = LocalizedStrings.Get(KEY_GAME_OVER);`.
