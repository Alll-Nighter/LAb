## Colour and Theme

### Overall Theme Decision

- **Theme:** Light mode only for the hackathon (clearer for demos on projectors/monitors).  
- **Vibe:** “Industrial safety dashboard” – clean, high-contrast, slightly technical, not playful.

Think: **Grafana-style safety ops dashboard** + **enterprise HSE (Health, Safety, Environment) tools**, not a startup landing page.

***

### Primary Color Palette (Use These Exact Hex Codes)

**Base / Background**
- Background (page): `#F5F7FA`  
- Surface (cards, panels): `#FFFFFF`  
- Border / Divider: `#E3E8EF`

**Primary Brand Color**
- Primary Blue (headers, primary buttons, highlights): `#2563EB`  
- Primary Blue (hover): `#1D4ED8`  

**Safety / Status Colors**
- Safe / OK: `#16A34A` (green)  
- Warning (minor issues, near-threshold): `#F59E0B` (amber)  
- Violation / Danger: `#DC2626` (red)  

**Text Colors**
- Primary text: `#0F172A` (almost black, high contrast)  
- Secondary text (labels, hints): `#475569` (slate gray)  
- Disabled / Muted text: `#94A3B8`

**Chart Colors (for Plotly/Altair)**
Use a consistent, non-default palette:

- Series 1: `#2563EB` (blue)  
- Series 2: `#DC2626` (red)  
- Series 3: `#16A34A` (green)  
- Series 4: `#F59E0B` (amber)  
- Series 5: `#7C3AED` (purple)  

Avoid Plotly’s default rainbow; explicitly set these in your chart configs.

***

### How to Apply Colors in Streamlit

Streamlit doesn’t allow full CSS control, but you can:

- Use `st.markdown` with inline HTML/CSS for:
  - Custom-colored metric cards.  
  - Section headers with primary blue.  
- Use status colors for:
  - Violation rows: red background or red left border.  
  - Safe states: green indicators.  

Example pattern (in `ui/app.py`):

```python
st.markdown(
    """
    <style>
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E3E8EF;
        border-radius: 8px;
        padding: 16px;
    }
    .metric-label {
        color: #475569;
        font-size: 14px;
    }
    .metric-value {
        color: #0F172A;
        font-size: 28px;
        font-weight: 700;
    }
    .violation-row {
        border-left: 4px solid #DC2626;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
```

Then wrap KPIs in `st.markdown('<div class="metric-card">...</div>', unsafe_allow_html=True)`.

***

## Fonts and Typography

### Font Family

Use a **single, clean sans-serif stack** that looks professional on all platforms:

- **Primary font:**  
  - `Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif`  

If you embed custom fonts (for slides/docs), use **Inter** (Google Fonts) as the main font.

In Streamlit, you can’t fully enforce fonts, but you can:

- Add a `<style>` block with:
  ```css
  html, body, [class*="css"] {
    font-family: "Inter", system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
  }
  h1, h2, h3 {
    font-weight: 700;
    letter-spacing: -0.02em;
  }
  ```

***

### Type Scale (Sizes & Usage)

Use this consistently for headings, body, labels, and numbers.

**Headings**
- `h1` (Page title: “Smart Lab Safety & PPE Compliance”)  
  - Size: `28–32px`  
  - Weight: `700`  
  - Color: `#0F172A`  

- `h2` (Section titles: “Live Camera Grid”, “AI Incident Report”)  
  - Size: `22–24px`  
  - Weight: `700`  
  - Color: `#0F172A`  

- `h3` (Subsections: “Violations per Zone”, “Ask Your Safety Data”)  
  - Size: `18–20px`  
  - Weight: `600`  
  - Color: `#0F172A`  

**Body Text**
- Primary body (descriptions, help text):  
  - Size: `15–16px`  
  - Weight: `400`  
  - Color: `#0F172A`  

- Secondary body (labels, axis titles, small notes):  
  - Size: `13–14px`  
  - Weight: `400`  
  - Color: `#475569`  

**Numbers / Metrics**
- KPI values (e.g., “27 Violations Today”):  
  - Size: `28–32px`  
  - Weight: `700`  
  - Color: `#0F172A`  
  - Optional: use primary blue `#2563EB` for key numbers to make them pop.

**Buttons**
- Button text:  
  - Size: `14–15px`  
  - Weight: `600`  
  - Color: `#FFFFFF` on primary buttons (blue background `#2563EB`).  

***

## Reference Look & Feel

Tell your AI tool / team:

> “Make the dashboard feel like a **Grafana safety ops panel** combined with an **enterprise HSE compliance tool**: clean, data-dense, high-contrast, with clear status colors. Not a marketing site, not a minimal startup landing page.”

Concrete references (for vibe, not to copy):

- **Grafana dashboards** (search “Grafana security dashboard” or “Grafana operations dashboard”):  
  - Dense information, clear panels, strong use of red/green for status.  
- **Enterprise safety platforms** (e.g., Enablon, Intelex, Cority – look at screenshots):  
  - Serious, industrial aesthetic, lots of tables, charts, and KPIs.  

Avoid:

- Overly rounded, “bubbly” UI.  
- Gradient-heavy, startup-landing-page looks.  
- Excessive white space that hides data.

***

## Component-Specific Styling Rules

### KPI Cards

- Background: `#FFFFFF`  
- Border: `1px solid #E3E8EF`  
- Border radius: `8px`  
- Padding: `16px`  
- Label: `14px`, `#475569`  
- Value: `28–32px`, `#0F172A` (or `#2563EB` for primary KPI).  

### Violations Table

- Header row:
  - Background: `#F9FAFB`  
  - Text: `14px`, `#475569`, weight `600`.  
- Body rows:
  - Text: `14px`, `#0F172A`.  
  - Alternating row background: `#FFFFFF` / `#F9FAFB`.  
  - Violation rows (severity = high): add left border `4px solid #DC2626`.  

### Charts

- Background: `#FFFFFF`  
- Grid lines: `#E3E8EF` (light).  
- Axis labels: `13px`, `#475569`.  
- Title: `16px`, `#0F172A`, weight `600`.  
- Use the defined chart color palette (blue, red, green, amber, purple).  
- No 3D effects, no shadows, no gradients.

### AI Report & Q&A Panels

- Panel background: `#FFFFFF`  
- Border: `1px solid #E3E8EF`  
- Border radius: `8px`  
- Padding: `16px`  
- Report text:
  - `15–16px`, `#0F172A`, line-height comfortable for reading.  
- Input box (Ask your safety data):
  - Border: `1px solid #E3E8EF`  
  - Focus border: `2px solid #2563EB`  
  - Placeholder text: `#94A3B8`.

***

## Light/Dark Mode Decision

- **Hackathon version:** Light mode only.  
  - More reliable on different projectors/monitors.  
  - Easier to keep contrast consistent in Streamlit.  
- **Future version (post-hackathon):**  
  - You can add dark mode later with a separate palette, but do **not** attempt this during the hackathon.

***
