# Logging Best Practices

**Purpose**: Centralized logging system documentation, GameLogger usage, and log level standards.
**Status**: 🟢 Active
**Tags**: #process, #standards, #logging

## Overview

Centralized logging using `GameLogger` class. Wraps Unity's Debug.Log with levels, context prefixes, and conditional compilation.

**Code Location**: `Scripts/Core/GameLogger.cs`

---

## Quick Reference

| # | Rule | Summary |
|---|---|---|
| [1](#log-levels) | **Log Levels** | Use appropriate levels (DevDebug to Error). |
| [2](#devdebug---the-throwaway-level) | **DevDebug** | Temporary tracing ONLY. Remove before commit. |
| [3](#usage-examples) | **Usage** | Use `GameLogger` class, not `Debug.Log`. |
| [4](#output-format) | **Format** | Context prefix `[Class.Method]` is automatic. |
| [5](#configuration) | **Config** | Set `MinLevel` for filtering (Editor vs Prod). |
| [6](#decision-tree) | **Decision Tree** | Guide for choosing the right log level. |

---

## Log Levels

| Level | Priority | Production | Color | When to Use |
|-------|----------|------------|-------|-------------|
| **DevDebug** | -1 | ❌ Stripped | 🔴 Red | TEMPORARY debugging. Remove when done! |
| **Debug** | 0 | ❌ Stripped | Gray | Development tracing, state changes |
| **Info** | 1 | ✅ Kept | Default | Normal operations, user actions |
| **Warning** | 2 | ✅ Kept | Yellow | Unexpected but recoverable |
| **Error** | 3 | ✅ Kept | Red | Failures, exceptions |

---

## DevDebug - The "Throwaway" Level

**Purpose**: When you're troubleshooting and need to add logging after every line to trace an issue.

```csharp
// Troubleshooting a puzzle generation bug
GameLogger.DevDebug("Starting generation");
var cells = GetEmptyCells();
GameLogger.DevDebug($"Found {cells.Count} empty cells");
var next = FindNextCell(cells);
GameLogger.DevDebug($"Next cell: {next?.Row},{next?.Col}");
// ... lots more temporary logging
```

**Rules**:
1. ✅ Use freely when debugging
2. ✅ Shows with red `[DEV]` prefix - easy to spot
3. ❌ Remove when done troubleshooting
4. ❌ Never commit to main branch with DevDebug calls
5. 💡 If you find old DevDebug calls, delete them - they're trash

**When to upgrade to Debug/Warn/Error**:
- If the log was actually useful → upgrade to `LogDebug`
- If it catches a real issue → upgrade to `LogWarning` or `LogError`
- If it's just noise → delete it

---

## Usage Examples

### DevDebug (Temporary)
```csharp
// Tracing an issue - DELETE these when done!
GameLogger.DevDebug("Got here 1");
GameLogger.DevDebug($"Value is: {myValue}");
GameLogger.DevDebug("About to call SomeMethod()");
```

### Debug (Development)
```csharp
GameLogger.LogDebug("Cell selected", this);
GameLogger.LogDebug($"Validating cell ({row},{col})");
```

### Info (Normal Operations)
```csharp
GameLogger.LogInfo("Game started");
GameLogger.LogInfo($"Puzzle loaded: {difficulty}");
GameLogger.LogInfo("User completed puzzle");
```

### Warning (Unexpected but OK)
```csharp
GameLogger.LogWarning("Theme not found, using default");
GameLogger.LogWarning("Save file missing, starting fresh");
```

### Error (Failures)
```csharp
GameLogger.LogError("Failed to generate valid puzzle");
GameLogger.LogError($"Invalid cell index: {index}");
GameLogger.LogException(ex, "Failed to save game", this);
```

---

## Output Format

```
[DEV] [GameBoard.GenerateLevel] Starting generation       ← DevDebug (red)
[DBG] [GridCell.SetValue] Setting value 5                 ← Debug (gray)
[SplashScreen.Start] Initialized                          ← Info (normal)
[ThemeManager.LoadSavedTheme] Theme not found             ← Warning (yellow)
[SaveManager.Save] Failed to write file                   ← Error (red)
```

The `[ClassName.MethodName]` prefix is **automatically added** using `[CallerFilePath]` and `[CallerMemberName]` attributes.

---

## Configuration

```csharp
// Show everything (default in Editor)
GameLogger.MinLevel = GameLogger.LogLevel.Debug;

// Production: Only warnings and errors
GameLogger.MinLevel = GameLogger.LogLevel.Warning;

// Disable all logging
GameLogger.MinLevel = GameLogger.LogLevel.None;
```

---

## Decision Tree

```
Is this temporary troubleshooting I'll remove?
└─ YES → DevDebug
└─ NO → Is this preventing functionality?
    └─ YES → Error
    └─ NO → Is this unexpected but handled?
        └─ YES → Warning
        └─ NO → Is this a normal operation?
            └─ YES → Info
            └─ NO → Debug
```

---

## Technical Details

### Conditional Compilation

`DevDebug` and `LogDebug` use `[Conditional]` attributes:
```csharp
[Conditional("UNITY_EDITOR"), Conditional("DEVELOPMENT_BUILD")]
```

This means:
- In **Editor** and **Development Builds**: Calls are included
- In **Release Builds**: Calls are **completely stripped** by the compiler (zero overhead)

### Automatic Context Prefix

Uses C# caller info attributes:
```csharp
[CallerFilePath] string filePath = ""   // Gets source file path
[CallerMemberName] string memberName = "" // Gets method name
```

The class name is extracted from the file path. No reflection needed!

---

**Remember**: DevDebug = Trash. Delete it when you're done debugging.

---

**Created**: December 5, 2025
**Status**: Active - Follow for all new code
