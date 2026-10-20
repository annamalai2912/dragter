# Contributing to Dragter

Thank you for your interest in contributing to **Dragter**, founded by **Annamalai KM**!

## How to Contribute

1. **Fork the Repository**:
   Fork [github.com/annamalai2912/dragter](https://github.com/annamalai2912/dragter) to your GitHub account.

2. **Clone & Set Up**:
   ```bash
   git clone https://github.com/<your-username>/dragter.git
   cd dragter
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Branching Guidelines**:
   - Create a feature branch: `git checkout -b feat/your-feature-name`
   - Create a bugfix branch: `git checkout -b fix/issue-description`

4. **Code Quality Standards**:
   - Run pyflakes: `python -m pyflakes dragter main.py`
   - Run test suite: `python main.py --test`
   - Preserve zero-latency performance ($<16\text{ms}$ per frame rendering).
   - Use clean typography and icon assets; avoid introducing emoji characters that trigger DirectWrite fallback latency.

5. **Submitting Changes**:
   - Commit with clear, descriptive messages:
     ```bash
     git commit -m "feat(ui): add new aspect ratio preset to crop tool"
     ```
   - Push to your fork and submit a Pull Request.

## Code of Conduct
Please be polite, constructive, and respectful to all community contributors and maintainers.
