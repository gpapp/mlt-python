@echo off
echo Building mlt-python...
uv build
if %ERRORLEVEL% NEQ 0 (
    echo Build failed!
    exit /b %ERRORLEVEL%
)

echo.
echo Build successful. Distributions in dist/
echo To publish to PyPI, run:
echo   uv publish
echo.
echo To publish to TestPyPI, run:
echo   uv publish --publish-url https://test.pypi.org/legacy/
echo.
pause
