
# Welspun WTT Executive Planning Console

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Source workbook
The app reads the workbook directly from:

```text
input/WTT.xlsx
```

## Project structure
- `app.py` - Streamlit entry point
- `wtt_app/config.py` - application constants and sheet mappings
- `wtt_app/core/formatters.py` - formatting and reusable display helpers
- `wtt_app/core/workbook.py` - workbook loading, session state, export, and WTT updates
- `wtt_app/calculations/summary.py` - Size_wise_details summary calculations
- `wtt_app/calculations/helpers.py` - LC, LH, DTA, JUKI, and Stenter helper calculations
- `wtt_app/calculations/links.py` - helper-driven updates back into the main WTT sheet
- `wtt_app/ui/styles.py` - executive styling
- `wtt_app/ui/components.py` - reusable UI blocks
- `wtt_app/ui/tabs.py` - tab rendering logic
