# Roblox Animation Tools

CLI tools for creating and analyzing Roblox NPC animations using Claude and Gemini, designed for Rojo workflows.

## Overview

This toolset enables a fully CLI-based animation workflow:

1. **Blender** (headless) - Author animations via Python scripting
2. **anim2rbx** - Convert FBX to Roblox KeyframeSequence
3. **Gemini Vision** - Analyze animation frames for quality feedback
4. **Rojo** - Sync animations to Roblox Studio
5. **IKControl** - Runtime terrain adaptation (Luau)

## Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                      ANIMATION AUTHORING (CLI)                      │
│                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐            │
│  │  Blender    │───▶│  Export     │───▶│  anim2rbx   │            │
│  │  --background│    │  .fbx       │    │  (Rust CLI) │            │
│  │  + bpy      │    │             │    │             │            │
│  └─────────────┘    └─────────────┘    └─────────────┘            │
│        │                                      │                    │
│        ▼                                      ▼                    │
│  ┌─────────────┐                       ┌─────────────┐            │
│  │   Gemini    │ ◀── Frame analysis    │  .rbxm      │            │
│  │   Vision    │                       │  (KeyframeSeq)│           │
│  └─────────────┘                       └──────┬──────┘            │
└──────────────────────────────────────────────┬────────────────────┘
                                               │
┌──────────────────────────────────────────────┼────────────────────┐
│                      ROJO WORKFLOW           │                     │
│                                              ▼                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐            │
│  │  animations/│    │  rojo serve │───▶│  Studio     │            │
│  │  *.rbxm     │───▶│             │    │  (live sync)│            │
│  └─────────────┘    └─────────────┘    └─────────────┘            │
└───────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────┐
│                      RUNTIME (Roblox)                              │
│                                                                    │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐           │
│  │  KeyframeSeq │───▶│  Register   │───▶│  Animation  │           │
│  │  from Rojo   │    │  TempId     │    │  Track      │           │
│  └─────────────┘    └─────────────┘    └──────┬──────┘           │
│                                               │                   │
│                                               ▼                   │
│                                        ┌─────────────┐           │
│                                        │  IKControl  │◀── Terrain│
│                                        │  (feet,body)│    Raycast│
│                                        └─────────────┘           │
└───────────────────────────────────────────────────────────────────┘
```

## Requirements

### External Tools

| Tool | Installation | Purpose |
|------|--------------|---------|
| [Blender](https://www.blender.org/) | `brew install --cask blender` | Animation authoring |
| [anim2rbx](https://github.com/jiwonz/anim2rbx) | `cargo install anim2rbx` | FBX → KeyframeSequence |
| [Lune](https://github.com/lune-org/lune) | `cargo install lune` | Programmatic Roblox DOM |
| [Rojo](https://rojo.space/) | `rokit add rojo-rbx/rojo` | Sync to Studio |

### API Keys

- `GEMINI_API_KEY` - For Gemini Vision analysis (get at https://aistudio.google.com/apikey)

## Project Structure

```
apps/roblox-animation/
├── README.md                    # This file
├── pyproject.toml              # Python dependencies
├── src/
│   ├── gemini_analyzer/        # Gemini image/frame analysis
│   │   ├── __init__.py
│   │   ├── single_image.py     # Analyze single image
│   │   └── frame_sequence.py   # Analyze animation frames
│   └── blender_scripts/        # Blender automation
│       ├── __init__.py
│       └── export_animation.py # Export to FBX
├── blender/                    # Blender project files
│   └── templates/
│       └── r15_rig.blend       # R15 rig template
├── scripts/
│   ├── convert_all.sh          # Batch FBX → rbxm conversion
│   └── render_frames.sh        # Render animation frames
└── tests/
    └── test_gemini_analyzer.py
```

## Gemini Tools

### 1. Single Image Analysis

Analyze any image (screenshot, render, reference):

```bash
uv run python -m gemini_analyzer.single_image \
  --image frame_024.png \
  --prompt "Analyze this animation frame for issues"
```

Use cases:
- Check for mesh clipping
- Verify pose correctness
- Compare against reference

### 2. Frame Sequence Analysis

Analyze animation as a series of frames:

```bash
uv run python -m gemini_analyzer.frame_sequence \
  --frames-dir ./renders/ \
  --fps 30 \
  --prompt "Analyze this walk cycle for smoothness and timing issues"
```

Use cases:
- Detect hitches/pops in animation
- Verify timing and weight shift
- Check ground contact accuracy

## Blender CLI Workflow

### Render Animation Frames

```bash
blender --background \
  --python blender/render_frames.py \
  -- input.blend output_dir/ --fps 30
```

### Export to FBX

```bash
blender --background \
  --python blender/export_animation.py \
  -- input.blend output.fbx
```

### Convert FBX to KeyframeSequence

```bash
anim2rbx animation.fbx -o animations/walk.rbxm
```

## Rojo Integration

### Project Configuration

Add to your `default.project.json`:

```json
{
  "tree": {
    "ReplicatedStorage": {
      "Animations": {
        "$path": "src/animations"
      }
    }
  }
}
```

### Playing Animations Without Publishing

In Studio (via Rojo sync), use `RegisterKeyframeSequence` for testing:

```lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local KeyframeSequenceProvider = game:GetService("KeyframeSequenceProvider")

-- Load KeyframeSequence synced via Rojo
local walkKfs = ReplicatedStorage.Animations:FindFirstChild("npc_walk")

-- Generate temporary animation ID (Studio only)
local tempAnimId = KeyframeSequenceProvider:RegisterKeyframeSequence(walkKfs)

-- Create and play animation
local animation = Instance.new("Animation")
animation.AnimationId = tempAnimId

local animator = npc.Humanoid:FindFirstChildOfClass("Animator")
local track = animator:LoadAnimation(animation)
track:Play()
```

**Note:** `RegisterKeyframeSequence` only works in Studio. Production requires publishing.

## Terrain Adaptation with IKControl

Animations cannot pre-bake terrain response. Use runtime IK:

```lua
local RunService = game:GetService("RunService")

local function setupTerrainIK(npc)
    local leftFoot = npc:FindFirstChild("LeftFoot")
    local rightFoot = npc:FindFirstChild("RightFoot")

    -- Create IK control for left foot
    local leftIK = Instance.new("IKControl")
    leftIK.Type = Enum.IKControlType.Position
    leftIK.EndEffector = leftFoot
    leftIK.ChainRoot = npc:FindFirstChild("LeftUpperLeg")
    leftIK.Parent = npc.Humanoid

    -- Create IK control for right foot
    local rightIK = Instance.new("IKControl")
    rightIK.Type = Enum.IKControlType.Position
    rightIK.EndEffector = rightFoot
    rightIK.ChainRoot = npc:FindFirstChild("RightUpperLeg")
    rightIK.Parent = npc.Humanoid

    -- Update IK targets based on terrain
    RunService.Heartbeat:Connect(function()
        local params = RaycastParams.new()
        params.FilterDescendantsInstances = {npc}

        -- Raycast down from each foot
        local leftRay = workspace:Raycast(
            leftFoot.Position + Vector3.new(0, 1, 0),
            Vector3.new(0, -3, 0),
            params
        )
        if leftRay then
            leftIK.Target = leftRay.Position
        end

        local rightRay = workspace:Raycast(
            rightFoot.Position + Vector3.new(0, 1, 0),
            Vector3.new(0, -3, 0),
            params
        )
        if rightRay then
            rightIK.Target = rightRay.Position
        end
    end)
end
```

## Gemini 3 Capabilities

### Image Analysis

- Granular control via `media_resolution` parameter (low/medium/high/ultra_high)
- Token costs: 70-280 tokens per image depending on resolution
- Up to 3,600 images per request

### Video/Animation Analysis

- Variable FPS: Default 1 FPS, supports >1 FPS for fast-action
- True video reasoning: understands *why* things happen, not just *what*
- 10 FPS captures fine details like "golf swing mechanics"

### Pricing (Gemini 3 Flash)

- Input: $0.50/1M tokens
- Output: $3/1M tokens

## CLI Tool Reference

### anim2rbx

Convert animation files to Roblox KeyframeSequence:

```bash
# Basic conversion
anim2rbx animation.fbx

# With output path
anim2rbx animation.fbx -o output.rbxm

# Verbose logging
anim2rbx animation.fbx -o output.rbxm --verbose

# Preserve identical poses
anim2rbx animation.fbx --no-filter
```

Supported input formats: FBX, COLLADA (.dae), glTF (.gltf/.glb), 3ds Max, Maya

### Lune (Roblox DOM manipulation)

Create KeyframeSequence programmatically:

```lua
-- create_animation.luau
local roblox = require("@lune/roblox")
local fs = require("@lune/fs")

local kfs = roblox.Instance.new("KeyframeSequence")
kfs.Name = "WalkCycle"

local keyframe = roblox.Instance.new("Keyframe")
keyframe.Time = 0
keyframe.Parent = kfs

local pose = roblox.Instance.new("Pose")
pose.Name = "LeftArm"
pose.CFrame = CFrame.Angles(0.5, 0, 0)
pose.Parent = keyframe

-- Save to file
local serialized = roblox.serializeModel({ kfs })
fs.writeFile("walk.rbxm", serialized)
```

Run with:

```bash
lune run create_animation.luau
```

## Research Sources

### Official Documentation

- [Roblox KeyframeSequence](https://create.roblox.com/docs/reference/engine/classes/KeyframeSequence)
- [Roblox IKControl](https://create.roblox.com/docs/reference/engine/classes/IKControl)
- [Gemini Image Understanding](https://ai.google.dev/gemini-api/docs/image-understanding)
- [Gemini Video Understanding](https://ai.google.dev/gemini-api/docs/video-understanding)
- [Rojo Sync Details](https://rojo.space/docs/v7/sync-details/)

### Tools

- [anim2rbx](https://github.com/jiwonz/anim2rbx) - Rust CLI for animation conversion
- [Lune](https://github.com/lune-org/lune) - Standalone Luau runtime
- [rbx-dom](https://dom.rojo.space/) - Roblox DOM format documentation

### Anthropic Engineering

- [Building Agents with Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)
- [Multi-Agent Research System](https://www.anthropic.com/engineering/multi-agent-research-system)

## Design Decisions

### Why Blender + anim2rbx (not Roblox native)?

| Requirement | Roblox Native | Blender + anim2rbx |
|-------------|---------------|---------------------|
| CLI automation | Poor (GUI-only) | Excellent |
| Rojo integration | N/A | .rbxm syncs |
| Claude/Gemini workflow | Manual | Fully automated |

### Why runtime IK for terrain?

Terrain is dynamic and unknown at animation authoring time. Standard game dev practice:
1. Base animations provide rhythm/timing
2. IK adjusts feet/body to actual terrain at runtime

### Why KeyframeSequence (not Animation asset)?

- KeyframeSequence can be synced via Rojo as .rbxm
- `RegisterKeyframeSequence` creates temp IDs for testing
- No publish step needed during development iteration

## Limitations

1. **Final publishing requires Studio GUI** - No CLI for animation asset upload
2. **RegisterKeyframeSequence is Studio-only** - Production needs published animations
3. **anim2rbx requires Assimp** - May need system library installation
