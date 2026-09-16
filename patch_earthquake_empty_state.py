from pathlib import Path

def patch(path_str, anchor, addition, label):
    path = Path(path_str)
    src = path.read_text(encoding="utf-8-sig")
    original = src
    if anchor not in src:
        raise SystemExit(f"ERROR: anchor not found for {label} in {path_str} -- printing file:\n" + src)
    src = src.replace(anchor, addition, 1)
    if src == original:
        print(f"{label}: no changes were necessary.")
    else:
        path.write_text(src, encoding="utf-8", newline="\n")
        print(f"{label}: patched successfully.")

FILE = "frontend/static/earthquakeengine.js"

# 1. Explicit "no events" state for the population note (currently stuck on
#    the static HTML placeholder when there is genuinely nothing to report)
patch(
    FILE,
    '            const popEl = document.getElementById("earthquakePopulationNote");\n'
    '            if (popEl && highestRisk) {\n'
    '                popEl.innerText = highestRisk.population_mode === "live"\n'
    '                    ? `${this.formatPopulation(highestRisk.population_exposed)} near highest-risk event (WorldPop ${highestRisk.population_year})`\n'
    '                    : "Click an event for live reading";\n'
    '            }',

    '            const popEl = document.getElementById("earthquakePopulationNote");\n'
    '            if (popEl) {\n'
    '                if (highestRisk) {\n'
    '                    popEl.innerText = highestRisk.population_mode === "live"\n'
    '                        ? `${this.formatPopulation(highestRisk.population_exposed)} near highest-risk event (WorldPop ${highestRisk.population_year})`\n'
    '                        : "Click an event for live reading";\n'
    '                } else {\n'
    '                    popEl.innerText = "No active events";\n'
    '                }\n'
    '            }',
    "earthquakeengine.js (explicit no-events population note)",
)

# 2. Distinguish a genuinely failed fetch from "still loading" -- currently
#    the catch block leaves every panel frozen on its initial placeholder text
patch(
    FILE,
    '        } catch (error) {\n'
    '            console.error("[Earthquake] live feed failed:", error);\n'
    '        }\n'
    '    },\n'
    '\n'
    '    async searchLocation(query) {',

    '        } catch (error) {\n'
    '            console.error("[Earthquake] live feed failed:", error);\n'
    '\n'
    '            const info = document.getElementById("earthquakeSceneInfo");\n'
    '            if (info) info.innerText = `Unable to reach earthquake feed -- last attempt ${new Date().toLocaleString()}`;\n'
    '\n'
    '            const countEl = document.getElementById("earthquakeCount");\n'
    '            if (countEl) countEl.innerText = "--";\n'
    '\n'
    '            const riskEl = document.getElementById("earthquakeHighestRisk");\n'
    '            if (riskEl) riskEl.innerText = "Unavailable";\n'
    '        }\n'
    '    },\n'
    '\n'
    '    async searchLocation(query) {',
    "earthquakeengine.js (explicit fetch-failure state)",
)

print()
print("EMPTY/FAILED STATE UI APPLIED -- hard refresh the browser to pick up the new JS.")
