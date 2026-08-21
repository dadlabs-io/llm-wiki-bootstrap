# User Settings Best Practices

**Purpose**: Reusable patterns for user-configurable settings (localization, themes, sounds, gameplay).
**Status**: 🟢 Active
**Tags**: #architecture, #standards

## Overview
This document defines patterns for user-configurable settings. These patterns are reusable across all apps.

**Goal**: Allow users to customize their experience (language, colors, sounds, etc.) with a consistent, maintainable architecture.

**Goal**: Allow users to customize their experience (language, colors, sounds, etc.) with a consistent, maintainable architecture.

---

## Quick Reference

| # | Rule | Summary |
|---|---|---|
| [1](#1-localization-language-settings) | **Localization** | `LocalizedStrings` + `LanguageData`. |
| [2](#2-themes-color-settings) | **Themes** | `ThemeManager` + `ThemeData` (ScriptableObject). |
| [3](#3-sound-settings) | **Sounds** | `SoundManager` + `SoundSettings` (PlayerPrefs). |
| [4](#4-gameplay-settings) | **Gameplay** | `GameplaySettings` static class wrapper for PlayerPrefs. |
| [5](#5-settings-persistence) | **Persistence** | Use `PlayerPrefs` with constants keys. |

---

## Settings Categories

| Category | Examples | User Can Change? |
|----------|----------|------------------|
| **Language** | UI text, button labels | ✅ Yes |
| **Theme/Colors** | Cell colors, backgrounds, text | ✅ Yes |
| **Sounds** | Sound effects, music, volume | ✅ Yes |
| **Gameplay** | Difficulty, hints, timer | ✅ Yes |
| **Display** | Font size, grid size | ✅ Yes |

---

## 1. Localization (Language Settings)

### Architecture

```
Scripts/Localization/
├── LocalizedStrings.cs    # String keys + Get() method
└── LanguageData.cs        # Language dictionaries

Assets/Localization/       # (Future: JSON files)
├── en.json
├── es.json
└── ...
```

### LocalizedStrings.cs
```csharp
public static class LocalizedStrings
{
    private static string _currentLanguage = "en";
    
    // String keys
    public static class Keys
    {
        public const string GameTitle = "game_title";
        public const string NewGame = "new_game";
        public const string Continue = "continue";
        public const string Settings = "settings";
        public const string Easy = "difficulty_easy";
        public const string Medium = "difficulty_medium";
        public const string Hard = "difficulty_hard";
        public const string Expert = "difficulty_expert";
        public const string YouWin = "you_win";
        public const string Hint = "hint";
        public const string Undo = "undo";
        // Add more as needed
    }
    
    public static string Get(string key) => LanguageData.GetString(_currentLanguage, key);
    public static void SetLanguage(string langCode) => _currentLanguage = langCode;
    public static string CurrentLanguage => _currentLanguage;
}
```

### LanguageData.cs (English Only for Now)
```csharp
public static class LanguageData
{
    private static Dictionary<string, Dictionary<string, string>> _languages = new()
    {
        ["en"] = new Dictionary<string, string>
        {
            ["game_title"] = "My App",
            ["new_game"] = "New Game",
            ["continue"] = "Continue",
            ["settings"] = "Settings",
            ["difficulty_easy"] = "Easy",
            ["difficulty_medium"] = "Medium",
            ["difficulty_hard"] = "Hard",
            ["difficulty_expert"] = "Expert",
            ["you_win"] = "You Win!",
            ["hint"] = "Hint",
            ["undo"] = "Undo"
        }
        // Add more languages later
    };
    
    public static string GetString(string lang, string key)
    {
        if (_languages.TryGetValue(lang, out var strings))
            if (strings.TryGetValue(key, out var value))
                return value;
        
        // Fallback to English, then show key
        if (_languages["en"].TryGetValue(key, out var fallback))
            return fallback;
        
        return $"[{key}]";
    }
    
    public static string[] GetAvailableLanguages() => _languages.Keys.ToArray();
}
```

### Usage
```csharp
titleText.text = LocalizedStrings.Get(LocalizedStrings.Keys.GameTitle);
```

---

## 2. Themes (Color Settings)

### Architecture

```
Scripts/Settings/
├── ThemeManager.cs        # Manages current theme
└── ThemeData.cs           # ScriptableObject definition

Assets/Themes/
├── DefaultLight.asset     # Light theme
├── DefaultDark.asset      # Dark theme
└── Custom/                # User-created themes (future)
```

### ThemeData.cs (ScriptableObject)
```csharp
[CreateAssetMenu(fileName = "Theme", menuName = "MyApp/Theme")]
public class ThemeData : ScriptableObject
{
    public string themeName = "Default";
    
    [Header("Cell Colors")]
    public Color cellDefault = new Color(0.95f, 0.95f, 1f);
    public Color cellSelected = new Color(0.8f, 0.8f, 1f);
    public Color cellHighlight = new Color(0.9f, 0.9f, 1f);
    public Color cellConflict = new Color(1f, 0.8f, 0.8f);
    public Color cellGiven = new Color(0.9f, 0.9f, 0.9f);
    
    [Header("Text Colors")]
    public Color textDefault = Color.black;
    public Color textGiven = new Color(0.2f, 0.2f, 0.2f);
    public Color textUser = new Color(0.2f, 0.4f, 0.8f);
    public Color textError = Color.red;
    public Color textNotes = Color.gray;
    
    [Header("UI Colors")]
    public Color background = Color.white;
    public Color gridLines = Color.black;
    public Color blockBorder = Color.black;
    public Color buttonNormal = new Color(0.9f, 0.9f, 0.9f);
    public Color buttonHighlight = new Color(0.8f, 0.8f, 1f);
}
```

### ThemeManager.cs
```csharp
public class ThemeManager : MonoBehaviour
{
    public static ThemeManager Instance { get; private set; }
    
    [SerializeField] private ThemeData[] availableThemes;
    [SerializeField] private ThemeData currentTheme;
    
    public ThemeData CurrentTheme => currentTheme;
    
    public event Action OnThemeChanged;
    
    private void Awake()
    {
        if (Instance == null) Instance = this;
        else Destroy(gameObject);
        
        LoadSavedTheme();
    }
    
    public void SetTheme(ThemeData theme)
    {
        currentTheme = theme;
        PlayerPrefs.SetString("theme", theme.themeName);
        OnThemeChanged?.Invoke();
    }
    
    private void LoadSavedTheme()
    {
        string savedTheme = PlayerPrefs.GetString("theme", "Default");
        currentTheme = availableThemes.FirstOrDefault(t => t.themeName == savedTheme) 
                       ?? availableThemes[0];
    }
}
```

### Usage
```csharp
cellImage.color = ThemeManager.Instance.CurrentTheme.cellDefault;
```

---

## 3. Sound Settings

### Architecture

```
Scripts/Settings/
├── SoundManager.cs        # Manages audio playback
└── SoundSettings.cs       # User preferences

Assets/Audio/
├── SFX/
│   ├── tap.wav
│   ├── success.wav
│   └── error.wav
└── Music/
    └── background.mp3
```

### SoundSettings (stored in PlayerPrefs)
```csharp
public static class SoundSettings
{
    private const string KEY_MASTER_VOLUME = "masterVolume";
    private const string KEY_SFX_ENABLED = "sfxEnabled";
    private const string KEY_MUSIC_ENABLED = "musicEnabled";
    
    public static float MasterVolume
    {
        get => PlayerPrefs.GetFloat(KEY_MASTER_VOLUME, 1f);
        set => PlayerPrefs.SetFloat(KEY_MASTER_VOLUME, Mathf.Clamp01(value));
    }
    
    public static bool SfxEnabled
    {
        get => PlayerPrefs.GetInt(KEY_SFX_ENABLED, 1) == 1;
        set => PlayerPrefs.SetInt(KEY_SFX_ENABLED, value ? 1 : 0);
    }
    
    public static bool MusicEnabled
    {
        get => PlayerPrefs.GetInt(KEY_MUSIC_ENABLED, 1) == 1;
        set => PlayerPrefs.SetInt(KEY_MUSIC_ENABLED, value ? 1 : 0);
    }
}
```

---

## 4. Gameplay Settings

### GameplaySettings.cs
```csharp
public static class GameplaySettings
{
    private const string KEY_SHOW_TIMER = "showTimer";
    private const string KEY_HIGHLIGHT_CONFLICTS = "highlightConflicts";
    private const string KEY_HIGHLIGHT_SAME_NUMBER = "highlightSameNumber";
    private const string KEY_AUTO_REMOVE_NOTES = "autoRemoveNotes";
    
    public static bool ShowTimer
    {
        get => PlayerPrefs.GetInt(KEY_SHOW_TIMER, 1) == 1;
        set => PlayerPrefs.SetInt(KEY_SHOW_TIMER, value ? 1 : 0);
    }
    
    public static bool HighlightConflicts
    {
        get => PlayerPrefs.GetInt(KEY_HIGHLIGHT_CONFLICTS, 1) == 1;
        set => PlayerPrefs.SetInt(KEY_HIGHLIGHT_CONFLICTS, value ? 1 : 0);
    }
    
    public static bool HighlightSameNumber
    {
        get => PlayerPrefs.GetInt(KEY_HIGHLIGHT_SAME_NUMBER, 1) == 1;
        set => PlayerPrefs.SetInt(KEY_HIGHLIGHT_SAME_NUMBER, value ? 1 : 0);
    }
    
    public static bool AutoRemoveNotes
    {
        get => PlayerPrefs.GetInt(KEY_AUTO_REMOVE_NOTES, 1) == 1;
        set => PlayerPrefs.SetInt(KEY_AUTO_REMOVE_NOTES, value ? 1 : 0);
    }
}
```

---

## 5. Settings Persistence

### Pattern: Use PlayerPrefs with Constants

```csharp
// In Constants/Strings.cs - All PlayerPrefs keys
public static class Strings
{
    // Settings keys
    public const string PrefLanguage = "language";
    public const string PrefTheme = "theme";
    public const string PrefMasterVolume = "masterVolume";
    public const string PrefSfxEnabled = "sfxEnabled";
    public const string PrefMusicEnabled = "musicEnabled";
    public const string PrefShowTimer = "showTimer";
    // ... etc
}
```

---

## Summary: Reusable Pattern

For any app, implement these managers:

| Manager | Responsibility |
|---------|----------------|
| `LocalizedStrings` | Text in user's language |
| `ThemeManager` | Colors, visual styling |
| `SoundManager` | Audio playback |
| `*Settings` classes | User preferences (PlayerPrefs) |

All settings should:
1. Have sensible defaults
2. Persist via PlayerPrefs
3. Be changeable from a Settings screen
4. Notify listeners when changed (events)

---

**Created**: December 5, 2025
**Status**: Active - Reusable pattern for all apps
