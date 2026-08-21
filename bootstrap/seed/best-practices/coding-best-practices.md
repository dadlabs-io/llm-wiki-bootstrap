# Coding Best Practices

**Purpose**: Coding standards, reference for error handling, naming conventions, and 1-based indexing rules.
**Status**: 🟢 Active
**Tags**: #process, #standards

## Overview

This document defines coding standards for the project. All code must follow these rules.

---

## Quick Reference

| #                                                 | Rule          | Summary                               |
| ------------------------------------------------- | ------------- | ------------------------------------- |
| [1](#1-exception-handling)                        | Exceptions    | Catch, log, handle all exceptions     |
| [2](#2-string-constants)                          | Strings       | No magic strings, use constants       |
| [3](#3-configurable-values-colors-fonts-sizes)    | Colors        | No hardcoded values, use ThemeManager |
| [4](#4-file-organization)                         | File Org      | Follow standard folder structure      |
| [5](#5-verify-api-contracts-before-using-classes) | API Contracts | Always verify classes/methods exist   |
| [6](#6-code-hygiene)                              | Code Hygiene  | Remove dead code immediately          |
| [7](#7-collection-types-list-vs-hashset)          | Collections   | Use List, UNLESS you need Contains()  |
| [8](#8-explicit-typing-no-var)                    | Typing        | Use explicit types, avoid `var`       |
| [9](#9-verify-imports-when-implementing-interfaces) | Imports     | Copy imports from working examples    |
| [10](#11-coordinates--indices)                    | Coordinates   | Use utility classes for coordinate conversions|
| [11](#12-avoid-type-switch-chains)                | Type Switches | Use virtual properties, not if-chains |

---

## 1. Exception Handling

### Rule: All Exceptions Must Be Caught, Logged, and Handled

**NEVER** leave exceptions unhandled or use empty catch blocks.

### ❌ BAD - Empty Catch

```csharp
try
{
    DoSomething();
}
catch (Exception)
{
    // Silent fail - FORBIDDEN
}
```

### ❌ BAD - Unlogged Exception

```csharp
try
{
    DoSomething();
}
catch (Exception ex)
{
    return false;  // Exception swallowed without logging - FORBIDDEN
}
```

### ✅ GOOD - Logged and Handled

```csharp
try
{
    DoSomething();
}
catch (Exception ex)
{
    GameLogger.LogError($"Failed to do something: {ex.Message}", this);
    // Handle gracefully (show user message, use fallback, etc.)
    return false;
}
```

### Safe Functions Pattern

Functions that handle exceptions internally and return success/failure are "safe functions":

```csharp
/// <summary>
/// Attempts to load puzzle. Returns true on success, false on failure.
/// This is a SAFE function - exceptions are handled internally.
/// </summary>
public bool TryLoadPuzzle(string puzzleData)
{
    try
    {
        // Parse and load puzzle
        return true;
    }
    catch (Exception ex)
    {
        GameLogger.LogError($"Failed: {ex.Message}", this);
        return false;
    }
}
```

---

## 2. String Constants

### Rule: No Magic Strings in Code

All strings must be in constants files.

| Category                                    | Location                                             |
| ------------------------------------------- | ---------------------------------------------------- |
| Scene names, PlayerPrefs keys, log prefixes | `Constants/Strings.cs`                               |
| User-facing text (UI)                       | `Localization/LocalizedStrings.cs`                   |
| Colors, themes                              | `ThemeManager` (see user-settings-best-practices.md) |

### ❌ BAD - Magic Strings

```csharp
titleText.text = "My App";
PlayerPrefs.SetInt("highScore", score);
SceneManager.LoadScene("MainMenu");
```

### ✅ GOOD - System Constants

```csharp
// In Constants/Strings.cs
public static class Strings
{
    // Scene names
    public const string MainMenuScene = "MainMenu";
    public const string GameScene = "Game";

    // PlayerPrefs keys
    public const string PrefHighScore = "highScore";
    public const string PrefLanguage = "language";
    public const string PrefTheme = "theme";
}
```

### ✅ GOOD - User-Facing Text (Localized)

```csharp
// Use LocalizedStrings for any text the user sees
titleText.text = LocalizedStrings.Get(LocalizedStrings.Keys.GameTitle);
```

**See `user-settings-best-practices.md` for full localization, themes, and sounds patterns.**

---

## 3. Configurable Values (Colors, Fonts, Sizes)

### Rule: All Visual Properties Must Be Centralized

Colors, fonts, sizes, and other visual properties must NOT be hardcoded.

### ❌ BAD - Hardcoded Colors

```csharp
cellBackground.color = new Color(0.9f, 0.9f, 1f);
errorText.color = Color.red;
```

### ✅ GOOD - Use ThemeManager

```csharp
// Get colors from the current theme
cellBackground.color = ThemeManager.Instance.CurrentTheme.cellDefault;
errorText.color = ThemeManager.Instance.CurrentTheme.textError;
```

**See `user-settings-best-practices.md` for ThemeManager and ThemeData patterns.**

---

## 4. File Organization

```
Scripts/
├── Constants/
│   └── Strings.cs            # Scene names, PlayerPrefs keys, etc.
├── Core/
│   └── GameLogger.cs         # Centralized logging
├── Localization/
│   ├── LocalizedStrings.cs   # User-facing text
│   └── LanguageData.cs       # Language data (English)
├── Settings/
│   ├── ThemeManager.cs       # Theme management
│   ├── ThemeData.cs          # ScriptableObject
│   ├── SoundSettings.cs      # Audio preferences
│   └── GameplaySettings.cs   # Gameplay preferences
```

**See `user-settings-best-practices.md` for details on each.**

---

## 5. Verify API Contracts Before Using Classes

### Rule: ALWAYS Verify Classes, Methods, and Properties Exist

Before using ANY class, method, or property, you MUST:

1. **Verify the class exists** in the codebase
2. **Verify the method/property exists** on that class
3. **Verify the type is correct** (return type, parameter types)
4. **NEVER guess or assume** - consult the actual class definition

This applies to ALL code, not just UI or database code. It's as fundamental as ensuring two operands in a mathematical expression are numbers.

### ❌ BAD - Guessing at API

```csharp
// Without checking ThemeData class definition:
Color primaryColor = ThemeManager.Instance.CurrentTheme.primary;  // WRONG - 'primary' doesn't exist!
```

### ✅ GOOD - Verify First

```csharp
// Step 1: Search for and read ThemeData.cs
// Step 2: Check available properties (colorNavy, buttonText, textError, etc.)
// Step 3: Use the correct property
Color textColor = ThemeManager.Instance.CurrentTheme.buttonText;  // CORRECT
```

### Process for Using Unknown Classes

1. **Search for the class definition**

   ```csharp
   // glob_file_search or codebase_search for "class ThemeData"
   ```

2. **Read the class file**

   ```csharp
   // Examine all public properties and methods
   // Document what's available
   ```

3. **Use only what exists**

   ```csharp
   // Reference only verified properties/methods
   ```

4. **Verify return types and parameters**
   ```csharp
   // Not just "does the method exist?" but "does it take these parameters?"
   // and "does it return what I expect?"
   ```

### Common Mistakes to Avoid

❌ **Guessing at property names:**

```csharp
obj.SomethingRandom  // Assumed this exists - it doesn't!
```

❌ **Assuming return types:**

```csharp
int count = GetItems().Length;  // Is GetItems() even nullable? What does it return?
```

❌ **Not checking method signatures:**

```csharp
puzzle.Load(id);  // Does Load() take an int? a string? A Puzzle object?
```

✅ **Verify everything:**

```csharp
// 1. Find Puzzle.cs
// 2. Verify: "public void Load(int puzzleId) { ... }"
// 3. Use it correctly
puzzle.Load(42);
```

---

## 6. Code Hygiene

### Rule: Remove Dead Code Immediately

**NEVER** leave commented-out code, unused methods, or obsolete code in the codebase.

### ❌ BAD - Commented Out Code

```csharp
// Old implementation - keeping just in case
// public void OldMethod()
// {
//     DoOldThing();
// }
```

### ❌ BAD - Unused Methods

```csharp
// Method exists but is never called from anywhere
private void UnusedHelper()
{
    // ...
}
```

### ✅ GOOD - Clean Code

- Delete unused methods, fields, and classes
- Remove commented-out code blocks
- Use version control (Git) to recover old code if needed
- If code "might be useful later," delete it - Git has history

---

## 7. Collection Types: List vs HashSet

### Rule: Use List, UNLESS You Need Contains()

**Default to `List<T>`**. Use `HashSet<T>` only when you need `Contains()` checks or automatic uniqueness.

**TL;DR:** `List<T>` by default → `HashSet<T>` if you need `Contains()` or uniqueness.

### When to Use List<T>

- ✅ **Default choice** - lighter weight, more flexible
- ✅ **Order matters** - maintains insertion order
- ✅ **Duplicates allowed** - can have multiple identical values
- ✅ **Indexed access** - can use `list[0]`, `list.Count`
- ✅ **Just iterating** - no Contains() checks needed
- ✅ **Small collections** - fine for small sets (like 1-9 numbers)

### When to Use HashSet<T>

- ✅ **Frequent Contains() checks** - O(1) vs O(n) for List
- ✅ **Automatic uniqueness** - prevents duplicates automatically
- ✅ **Order doesn't matter** - no guaranteed order
- ✅ **Membership testing** - checking if value exists in collection

### Performance Comparison

| Operation      | List<T>       | HashSet<T>   |
| -------------- | ------------- | ------------ |
| **Contains()** | O(n) - slow   | O(1) - fast  |
| **Add()**      | O(1) at end   | O(1) average |
| **Memory**     | ✅ Lighter    | ❌ Heavier   |
| **Order**      | ✅ Guaranteed | ❌ No order  |
| **Duplicates** | ✅ Allowed    | ❌ Prevented |

### Examples

#### ✅ GOOD - List for Simple Collection

```csharp
// Just returning a collection, no Contains() checks
public List<int> ToList()
{
    List<int> list = new List<int>(9);
    for (int i = 1; i <= 9; i++)
    {
        if (Has(i))
        {
            list.Add(i);
        }
    }
    return list;
}
```

#### ✅ GOOD - HashSet for Membership Checks

```csharp
// Need to check if numbers exist, and ensure uniqueness
HashSet<int> usedNumbers = new HashSet<int>();
foreach (GridCell cell in rowCells)
{
    if (cell.IsAnswerMode)
    {
        usedNumbers.Add(cell.CurrentValue);  // Automatic uniqueness
    }
}

// Fast Contains() check
if (usedNumbers.Contains(5))
{
    // Number 5 is already used
}
```

#### ❌ BAD - List for Frequent Contains()

```csharp
// Slow - O(n) for each Contains() check
List<int> usedNumbers = new List<int>();
if (!usedNumbers.Contains(5))  // Slow for large lists!
{
    usedNumbers.Add(5);
}
```

### Decision Tree

```
Need to check Contains() frequently?
├─ YES → Use HashSet<T>
└─ NO → Need uniqueness automatically?
    ├─ YES → Use HashSet<T>
    └─ NO → Use List<T> (default)
```

---

---

## 8. Explicit Typing (No `var`)

### Rule: Use Explicit Types, Avoid `var`

**Always favour explicit typing** (`OrderItem item`) over implicit typing (`var item`).
The only exception is when the type is *extremely* verbose and obvious (e.g., `Dictionary<string, List<int>>`), but even then, explicit definitions are preferred for clarity.

### Why?
1.  **Readability**: `OrderItem item` tells you exactly what the variable is. `var item` forces you to guess or check the method signature.
2.  **Ambiguity**: `var result = GetResult()` hides whether `result` is an object, a struct, an int, or null. Explicit typing exposes this immediately.
3.  **Safety**: If an API changes (e.g. `GetCell` returns `int` instead of `Cell`), explicit typing catches it immediately at the declaration line.

### ❌ BAD - Vague Typing

```csharp
var cell = board.GetCell(i);      // What is 'cell'?
var result = solver.Solve(puz);   // Is result a bool? A class? An enum?
var items = GetItems();           // List? Array? IEnumerable?
```

### ✅ GOOD - Explicit Typing

```csharp
GridCell cell = board.GetCell(i);              // Crystal clear
SingleStepSolution result = solver.Solve(puz);   // Explicit contract
List<string> items = GetItems();                 // Known collection type
```


---

## 9. Verify Imports When Implementing Interfaces

### Rule: Always Copy Imports from Working Examples

When creating a new file that implements an interface, **ALWAYS** verify the required `using` statements by checking an existing file that implements the same interface.

### Why?

Interfaces often use types from external libraries or other namespaces. The interface definition itself doesn't tell you which namespaces contain the parameter types. Designing from scratch leads to missing imports.

### Real Example: NewFeatureHandler.cs

**The Problem**: Created `NewFeatureHandler : IGameStrategy` with `CreateHint(SingleStepSolution, GameState, GameBoard)` but forgot that `GameState` is in `GameEngine.Models`, not `GameEngine`.

**The Fix**: Check `ExistingHandler.cs` (another `IGameStrategy` implementation) to see it has:
```csharp
using GameEngine.Models;  // Contains GameState
```

### ❌ BAD - Design from Scratch

```csharp
// "I'll just add the imports I think I need"
using GameEngine;  // Missing GameEngine.Models!

public class NewFeatureHandler : IGameStrategy
{
    public Hint CreateHint(SingleStepSolution result, GameState state, GameBoard board)
    //                                               ^^^^^^^^^ CS0246: Type not found!
```

### ✅ GOOD - Copy from Working Example

```csharp
// Step 1: Find existing implementation (ExistingHandler.cs)
// Step 2: Copy its using statements
// Step 3: Add any new ones you need

using GameEngine;
using GameEngine.Models;  // Copied from ExistingHandler - contains GameState
using MyApp.Core.Features;
// ... etc
```

### Process for New Interface Implementations

1. **Find an existing implementation** of the same interface
2. **Copy ALL using statements** from that file
3. **Add any additional imports** your implementation needs
4. **Verify compilation** before proceeding

This applies to:
- New strategy pattern implementations (`IGameStrategy`)
- New feature implementations (`IGameFeature`)
- New Hint implementations (base `Hint` class)
- Any other interface or base class implementations

---

## 11. Coordinates & Indices

### Rule: ALWAYS Use Utility Classes for Conversions

**NEVER** manually calculate Row, Column, or Block indices using arithmetic (`/ 9`, `% 9`) in feature code.
Different parts of the engine use different standards (0-based vs 1-based), and manual math is prone to off-by-one errors.

### ❌ BAD - Manual Math
```csharp
// Fragile: Assumes 0-based index. If 1-based index (1-81) is passed, this fails.
int row = cellIndex / 9; 
int col = cellIndex % 9;
```

### ✅ GOOD - Use Utility
```csharp
// Robust: Handles the conversion logic centrally
int row = GridUtility.GetRowFromIndex(cellIndex);
int col = GridUtility.GetColumnFromIndex(cellIndex);
var (houseType, houseIndex) = GridUtility.GetSectionInfo(hIdx);
```

---

## 12. Avoid Type-Switch Chains

### Rule: Replace Cascading Type Checks with Virtual Properties

When handling multiple types that inherit from a common base, **do not** use cascading `if (x is Type)` checks. This violates the Open-Closed Principle and requires modification whenever a new type is added.

### ❌ BAD - Type-Switch Chain
```csharp
// Easy to forget a type, no compile-time safety
if (hint is NoteValidationHint noteHint) { ... }
else if (hint is LockedCandidatesHint lockedHint) { ... }
else if (hint is NakedCandidateHint nakedHint) { ... }
// ... grows with each new hint type
```

### ✅ GOOD - Virtual Properties on Base Class
```csharp
// Base class defines virtual properties with safe defaults
public abstract class Hint
{
    public virtual Dictionary<int, List<int>> NotesToRemove => new();
    public virtual Dictionary<int, List<int>> NotesToAdd => new();
    public bool HasNoteChanges => NotesToRemove.Count > 0 || NotesToAdd.Count > 0;
}

// Handler is now type-agnostic
if (hint.HasNoteChanges)
{
    ApplyNoteChanges(hint.NotesToRemove, hint.NotesToAdd);
}
```

### Benefits
- **Compile-time safety**: Missing implementations are caught during development
- **Open-Closed**: New hint types don't require modifying the handler
- **Single Responsibility**: Each hint knows its own data

### When to Apply
- Any place with 3+ `if (x is Type)` checks
- When new types are added regularly
- When the type check is followed by accessing type-specific properties

---

## 13. Summary Checklist

Before committing code, verify:

- [ ] **API Contracts**: Every class, method, and property used is verified to exist
- [ ] **Interface Imports**: New interface implementations copy imports from working examples
- [ ] **Type Safety**: Return types and parameters match expectations
- [ ] **Exceptions**: All try/catch blocks log the exception with context
- [ ] **No empty catches**: Every catch block has logging + handling
- [ ] **No magic strings**: Use `Strings.cs` for system strings
- [ ] **User-facing text**: Use `LocalizedStrings.Get()` for UI text
- [ ] **No hardcoded colors**: Use `ThemeManager` for colors
- [ ] **No hardcoded values**: Use constants or settings classes
- [ ] **No dead code**: Remove unused methods, commented code, obsolete code
- [ ] **No DevDebug calls**: Remove temporary debugging before committing

---

**Created**: December 5, 2025
**Updated**: January 20, 2026 - Added Rule 12 (Avoid Type-Switch Chains)
**Status**: Active - Follow for all new code
