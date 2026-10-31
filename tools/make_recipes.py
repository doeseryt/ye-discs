#!/usr/bin/env python3
"""Generate recipe JSONs for ye discs.

The pressing craft: coal + paper (a blank vinyl) around a core item that
identifies the album era. Result: the album's disc.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REC = os.path.join(ROOT, "src", "main", "resources", "data", "ye_discs", "recipes")
os.makedirs(REC, exist_ok=True)

CORES = {
    "college_dropout":    "minecraft:leather",         # bear's jacket
    "late_registration":  "minecraft:note_block",      # orchestral
    "graduation":         "minecraft:firework_rocket", # arena celebration
    "808s":               "minecraft:packed_ice",      # frozen heart
    "mbdtf":              "minecraft:netherite_scrap", # dark maximalism
    "watch_the_throne":   "minecraft:gold_block",      # opulent brass
    "yeezus":             "minecraft:iron_block",      # brutalist metal
    "tlop":               "minecraft:pink_dye",        # faded pink scribble
    "ye":                 "minecraft:grass_block",     # wyoming field
    "jik":                "minecraft:lapis_lazuli",    # gospel water blue
    "donda":              "minecraft:black_wool",      # mourning black
    "donda2":             "minecraft:gray_dye",        # stem-player
    "vultures1":          "minecraft:bone",            # vulture bone
    "vultures2":          "minecraft:bone_meal",       # hollowed sequel
    "bully_era":          "minecraft:gold_ingot",      # dusty gold — BULLY
}

def disc_item(name):
    return "ye_discs:ye_disc_" + name

for name, core in CORES.items():
    recipe = {
        "type": "minecraft:crafting_shaped",
        "pattern": ["CPC", "PIP", "CPC"],
        "key": {
            "C": {"item": "minecraft:coal"},
            "P": {"item": "minecraft:paper"},
            "I": {"item": core},
        },
        "result": {"item": disc_item(name), "count": 1},
    }
    with open(os.path.join(REC, f"ye_disc_{name}.json"), "w", encoding="utf-8") as f:
        json.dump(recipe, f, indent=2)
    print("recipe:", name, "core:", core)
