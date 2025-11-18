# VibeDNA: Custom DNA Generator for Blender
Create a 3d DNA molecule with adjustable parameter using this addon


![VibeDNA Plugin Demo](https://github.com/LucasSilvaFerreira/VibeDnaBlenderAddon/raw/main/blendervibe.jpg)

**VibeDNA** is a powerful Blender Add-on designed to procedurally generate customizable 3D DNA double helices. This tool is ideal for scientific visualization, medical animation, and motion graphics, offering advanced controls for unwinding (topoisomerase simulation), custom text labels, and emissive materials.

## ✨ Features

* **Parametric Generation:** Fully non-destructive control over helix radius, pitch, base pair height, and backbone thickness.
* **🧬 Accurate Pairing:** Randomly generates Nucleotides with correct biological pairings (Adenine-Thymine / Guanine-Cytosine).
* **🔄 Animation Ready:** Includes "Unwind" sliders to simulate DNA replication, denaturation, or transcription processes.
* **🏷️ Smart Labeling:**
    * **Double-Sided:** Base letters are visible from both the front and back of the nucleotide.
    * **Auto-Orientation:** Labels automatically rotate to remain upright (vertical) regardless of the helix twist or camera angle.
* **🎨 Material Controls:**
    * Customize colors for all 4 bases and the backbones.
    * **Emission Control:** Add a glowing effect to the text labels directly from the UI using the `Text Emission` slider.

## 📦 Installation

1.  Download the `dna_generator.py` file from this repository.
2.  Open Blender (Version 3.0 or higher).
3.  Go to **Edit > Preferences > Add-ons**.
4.  Click **Install...** and select the downloaded `.py` file.
5.  Search for **"Custom DNA Generator"** and check the box to enable it.

## 🚀 Usage

1.  In the 3D Viewport, press `N` to open the **Sidebar**.
2.  Click on the **DNA Tool** tab.
3.  Adjust the **Configuration Parameters**:
    * **Geometry:** Controls the physical size and twist of the helix.
    * **Rotation & Unwinding:** Use `Unwind Start %` and `Unwind End %` to straighten specific sections of the strand.
    * **Labels & Emission:** Increase `Label Scale` for visibility and `Text Emission` to make letters glow.
4.  Click the **Generate DNA** button.

## ⚙️ Parameters

| Parameter | Description |
| :--- | :--- |
| **Helix Radius** | The width of the double helix structure. |
| **Pitch** | The distance of one complete turn of the helix. |
| **Num Base Pairs** | The total length (number of rungs) of the DNA strand. |
| **Unwind Start/End** | Determines the range (0.0 to 1.0) where the DNA untwists. |
| **Text Emission** | Controls the strength of the light emitted by the nucleotide letters. |
| **Gap Fill** | Controls how close the nucleotide rungs get to the backbone (1.0 = touching). |

## 🔧 Requirements

* **Blender 3.0+**

## 📄 License

This project is licensed under the MIT License.