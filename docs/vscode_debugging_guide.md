# VS Code Debugging Setup Guide

## 🐛 Debug Configurations Available

VS Code is now configured with comprehensive debugging support for the Battle AI project. Here are the available configurations:

### 1. **Python: Current File**

- **Use**: Debug any Python file you're currently editing
- **How**: Open any `.py` file, press `F5`, select this configuration
- **Great for**: Testing individual modules, exploring code

### 2. **Python: Run Tests**

- **Use**: Debug all tests in the `tests/` directory
- **How**: Press `F5`, select this configuration
- **Great for**: Finding test failures, understanding test flow

### 3. **Python: Run Specific Test File**

- **Use**: Debug the specific test file you're currently viewing
- **How**: Open a test file (e.g., `test_vector2d.py`), press `F5`
- **Great for**: Focused test debugging

### 4. **Python: Debug Utils**

- **Use**: Run the debug utility file to test project setup
- **How**: Press `F5`, select this configuration
- **Great for**: Verifying everything works, exploring data structures

### 5. **Future Configurations**

- **Battle AI Main**: Will debug the main simulation (when created)
- **Agent Test Simulation**: Will debug agent testing scenarios

## 🚀 Quick Start Debugging

### Test the Setup Right Now:

1. **Open `debug_utils.py`**
2. **Set a breakpoint** on line with `breakpoint_marker = "Set breakpoint on this line"`
3. **Press F5** and select "Python: Debug Utils"
4. **Step through** the code to see Vector2D and Config in action

### Debugging Your Own Code:

1. **Open any Python file** (e.g., `src/utils/vector2d.py`)
2. **Click in the margin** to set breakpoints (red dots)
3. **Press F5** and select "Python: Current File"
4. **Use debug controls**:
   - `F10` - Step over
   - `F11` - Step into
   - `Shift+F11` - Step out
   - `F5` - Continue

## 📋 VS Code Tasks Available

Access these via `Ctrl+Shift+P` → "Tasks: Run Task":

### Testing Tasks:

- **Run Tests** - Execute all tests
- **Run Tests with Coverage** - Generate coverage report

### Code Quality Tasks:

- **Format Code (Black)** - Auto-format all Python code
- **Lint Code (Flake8)** - Check code style and errors
- **Type Check (MyPy)** - Verify type annotations
- **Full Code Quality Check** - Run all quality checks in sequence

### Maintenance Tasks:

- **Install Dependencies** - Reinstall requirements.txt
- **Clean Cache** - Remove **pycache** and other temp files

## 🔧 IDE Features Configured

### Auto-formatting:

- **Black formatter** runs on save
- **Import organization** on save
- **88-character line limit** (PEP 8 extended)

### Testing Integration:

- **pytest discovery** automatic
- **Test runner** in side panel
- **Test debugging** with breakpoints

### Linting & Type Checking:

- **Flake8** for code style
- **MyPy** for type checking
- **Auto-completion** with IntelliSense

### Environment:

- **Virtual environment** automatically detected
- **PYTHONPATH** properly configured
- **Terminal** activates venv automatically

## 🎯 Debugging Best Practices

### 1. Use Breakpoints Effectively:

```python
# Set breakpoints on interesting lines
position = Vector2D(x, y)  # <- Breakpoint here
velocity = calculate_velocity(target)  # <- And here
```

### 2. Inspect Variables:

- **Variables panel** shows all local/global variables
- **Watch panel** for monitoring specific expressions
- **Debug console** for executing code during debugging

### 3. Step Through Code:

- **Step Into** functions to understand behavior
- **Step Over** to skip function details
- **Step Out** to return to caller

### 4. Debug Tests:

```python
def test_vector_math():
    v1 = Vector2D(3, 4)  # <- Breakpoint here
    assert v1.magnitude() == 5.0  # <- Inspect v1 in Variables panel
```

## 🧪 Testing Your Debug Setup

### Run this command to verify everything works:

1. Open Command Palette (`Ctrl+Shift+P`)
2. Type "Tasks: Run Task"
3. Select "Run Tests"
4. Should see all tests passing

### Or debug interactively:

1. Open `debug_utils.py`
2. Set breakpoints in the test functions
3. Press `F5` → Select "Python: Debug Utils"
4. Explore variables and step through code

## 📁 Files Created

Your `.vscode/` directory now contains:

- `launch.json` - Debug configurations
- `settings.json` - Project settings and Python configuration
- `tasks.json` - Build and test tasks
- `extensions.json` - Recommended extensions

## 🔍 Troubleshooting

### Python Not Found:

- Check that `settings.json` points to correct venv path
- Restart VS Code after Python installation

### Tests Not Discovered:

- Ensure pytest is installed: Run "Install Dependencies" task
- Check that test files start with `test_`

### Breakpoints Not Hit:

- Verify the correct debug configuration is selected
- Check that PYTHONPATH includes project root

### IntelliSense Not Working:

- Select correct Python interpreter: `Ctrl+Shift+P` → "Python: Select Interpreter"
- Choose the venv interpreter: `./venv/Scripts/python.exe`

---

🎉 **You're now ready for professional Python debugging!** Your VS Code is configured with industry-standard tools and practices for AI development.
