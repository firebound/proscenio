# SPEC 013 - Weight paint ergonomics + automesh

Status: **research complete, decisions locked, ready for TODO Wave 13.1**. Survey covers 9 tools (Spine, DragonBones, Spriter, Live2D Cubism, Moho, Toon Boom Harmony, Adobe Animate, Blender native, COA Tools 2) + community-pain synthesis across BlenderArtists / Reddit / Blender Stack Exchange / Spine forums / Adobe Community / Toon Boom learn / Cubism docs. 16 design decisions locked (D1-D16).

## Problem

Proscenio's downstream pipeline for skinned meshes is already wired end-to-end. [SPEC 003 (Skinning weights)](../003-skinning-weights/STUDY.md) shipped the writer (`_build_sprite_weights` normalizes per-vertex sums and emits the bone-major `weights` array) + the Godot importer (`polygon_builder.gd` branches into `Polygon2D.skeleton` + `add_bone()` when `weights` are present). A vertex group named after a bone in Blender becomes a real weighted influence in Godot at import time, with zero extra ceremony.

What is missing is the **upstream half**: the authoring experience that produces those vertex groups in the first place. Today the only path is *vanilla Blender weight paint*, which was designed for 3D character rigging and is hostile in four documented ways for 2D cutout work:

1. **No automesh.** A 2D sprite enters the addon as a single rectangular plane (4 vertices). To deform smoothly under a bone chain the user must subdivide the plane manually, knife-cut around the silhouette, or import from Photoshop and hope the polygon import (SPEC 011) produces enough vertices to bend. There is no Proscenio operator that turns "this PNG with alpha" into "a deformable mesh that follows the alpha boundary with N vertices of density I picked." COA Tools 2 ships exactly this operator ([automesh.py `COATOOLS2_OT_AutomeshFromTexture`](https://github.com/Aodaruma/coa_tools2/blob/master/coa_tools2/operators/automesh.py)) and the wider 2D community treats it as table stakes: Spine `Trace` ([Mesh attachments](http://esotericsoftware.com/spine-meshes)), Live2D Cubism Automatic Mesh Generation ([mesh-edit doc](https://docs.live2d.com/en/cubism-editor-manual/mesh-edit/)), Adobe Animate Asset Warp auto-triangulation ([Asset Warp](https://helpx.adobe.com/animate/how-to/asset-warp.html)).
2. **Auto-weights fails on planar meshes.** Blender's "Parent with Automatic Weights" (`Ctrl+P` -> Automatic) uses bone-heat surface diffusion. On a planar 2D mesh (everything at Y=0) the heat solver routinely fails with `Bone Heat Weighting: failed to find solution for one or more bones` and silently leaves vertex groups empty - documented in [T45493](https://developer.blender.org/T45493) ("none of the vertices in an island being visible to any bones"), [T70834](https://developer.blender.org/T70834) (precision failure at distance from origin), [T37685](https://developer.blender.org/T37685) (normal-recalc dependency), [T51250](https://developer.blender.org/T51250), and [#127345](https://projects.blender.org/blender/blender/issues/127345). The error is the single most-asked Blender weight question on Stack Exchange. The Envelope path works but bleeds across body-part boundaries because every bone's envelope capsule reaches the neighboring limb. The user is left to paint every weight manually from zero.
3. **Weight paint brush UX is 3D-centric.** Brush radius is in world units (does not scale with 2D ortho zoom level), `X-Axis Mirror` is per-brush rather than per-mode ([T46254](https://developer.blender.org/T46254), [#116115](https://projects.blender.org/blender/blender/issues/116115)), the Gradient tool ignores X-Symmetry entirely ([T99668](https://developer.blender.org/T99668)), the **Front Faces Only** default silently breaks every stroke on a thin plane ([devtalk: "Painting through the mesh is not intuitive or user friendly"](https://devtalk.blender.org/t/painting-through-the-mesh-is-not-intuitive-or-user-friendly/15231)), and the heatmap viz is invisible on low-poly meshes. Pen tablet pressure has a graveyard of bugs ([T82432](https://developer.blender.org/T82432), [T73377](https://developer.blender.org/T73377), [T93069](https://developer.blender.org/T93069)) and Blur+Smudge currently crash on undo in Blender 4.5 ([#149138](https://projects.blender.org/blender/blender/issues/149138)).
4. **Iteration destroys weights.** Changing mesh density after binding wipes vertex group data. Blender's voxel remesher [explicitly states](https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/remesh.html) only face sets and mask survive; everything else is deleted by design. Issue [#150016](https://projects.blender.org/blender/blender/issues/150016) tracks an active regression where remesh demotes vertex groups to plain attributes. The official remedy is the Data Transfer modifier whose "Nearest Face Interpolated" mode is itself unreliable - an entire third-party-addon market ([Robust Weight Transfer](https://80.lv/articles/grab-this-one-click-blender-tool-for-effortless-weight-transfers) builds on SIGGRAPH ASIA 2023 paper "Robust Skin Weights Transfer via Weight Inpainting") exists exclusively to paper over this gap.

The combined effect: SPEC 003 is technically usable, but actually authoring a skinned character today means hours of manual subdivision + manual weight painting per sprite, redone from scratch any time the mesh changes. The pipeline ships skinning capability; the addon does not yet ship skinning ergonomics. SPEC 013 closes that gap.

Concrete observed scenarios that this SPEC must enable in under 30 seconds each:

- "Turn this hand PNG into a 200-vertex mesh that bends at the wrist." (automesh)
- "Bind this arm mesh to the 3-bone arm chain I just drew with Quick Armature." (auto-vertex-groups from bone chain + planar-safe seed)
- "Smooth the weights at the elbow so the bend looks fluid." (brush polish in 2D-aware mode)
- "I regenerated the mesh at higher density - keep my hand-painted weights." (iteration loop preserve)
- "Mirror these arm weights to the other side." (paint-from-rig preset)

None of these are exotic asks. All of them are blocked today.

## Constraints

- **Blender-only authoring.** All operators run in `bpy.types.Operator`; no GDExtension, no native code. SPEC 013 cannot push native shaders or compute kernels into the runtime path; mesh + weight authoring happens at editor time and persists as vertex groups + mesh data on the `.blend`.
- **Strong typing.** Per [`.ai/conventions.md`](../../.ai/conventions.md) static-typing section: every parameter typed, every return typed, `Any` only at the `bpy` boundary. Mypy strict.
- **No schema or format-version bump.** Downstream output (`weights` array on the sprite) is unchanged - SPEC 003 already defines it. SPEC 013 is purely authoring side; the `.proscenio` shape does not move.
- **XZ picture-plane convention is law.** Like Quick Armature (SPEC 012), automesh outputs lie on Y=0. Mesh density and weight gradients must respect that the working surface is planar.
- **No third-party Python dependencies at runtime.** This constraint is load-bearing - COA Tools 2's hard dependency on `cv2` + `numpy` is its single biggest adoption blocker ([issues #94](https://github.com/Aodaruma/coa_tools2/issues/94) and [#107](https://github.com/Aodaruma/coa_tools2/issues/107) - corp / ISP firewalls block PyPI, manual cv2 copy breaks numpy ABI, addon errors out before the user can try the feature). Mesh generation has to use Blender's built-in `bmesh` + `mathutils` + pure-Python alpha-contour walking (Moore neighbour or marching squares on the alpha channel via the existing `bpy.types.Image.pixels` buffer). Allowed at *test* time for fixture preparation only.
- **Coexist with vanilla Blender weight paint.** Users with prior Blender muscle memory must be able to drop into `Weight Paint` mode and use the brush as usual. SPEC 013 adds helpers around that mode; it does not replace it.
- **Coexist with Photoshop importer (SPEC 011).** Imported `[mesh]`-tagged layers already arrive as `Polygon2D`-shaped meshes via the planner. Automesh must accept both "single plane in" and "imported polygon in" and add density without destroying the existing topology or the `proscenio_psd_kind = "mesh"` custom property.
- **Quick Armature interop (SPEC 012).** A user who just drew a 3-bone arm with `proscenio.quick_armature` should be one click away from "create vertex groups for these bones on the selected mesh + initialize them empty so I can start painting." The "active armature picker" contract from SPEC 012 D16 is the source of truth.
- **Reload safety.** Operators must register / unregister cleanly with the addon's reload-scripts loop. State that lives between invocations stays in PropertyGroups or Scene custom properties, not in module-level globals (lessons from SPEC 012 PEP-563 bug).
- **ESC always exits any modal.** Hard contract. COA Tools 2's Draw 2D Polygon modal ([edit_mesh.py:1571](https://github.com/Aodaruma/coa_tools2/blob/master/coa_tools2/operators/edit_mesh.py)) makes ESC a deselect-only - confirmed root cause of the "stroke continues on pen tablet after Esc" bug from the user-supplied Discord screenshot. SPEC 013 modals must (a) treat ESC as both "release the pending stroke" AND "exit the modal", (b) handle `WINDOW_DEACTIVATE`, (c) detect tablet release via `event.pressure == 0` + a timer fallback.

## Reference: 2D rigging tooling survey (automesh + weight + bind)

Nine tools categorized by paradigm:

- **Bone + per-vertex weight** (Proscenio's category): Spine, DragonBones, Blender native, COA Tools 2.
- **Bone + region/influence** (no per-vertex weights): Adobe Animate (soft/hard bone toggle + mesh density), Moho (bone strength region + smart bone actions).
- **Hybrid deformer chains + region blend**: Toon Boom Harmony (Bone + Curve + Envelope + Weighted Deform + Auto-Patch).
- **Deformer hierarchy reparent** (no bones at all): Live2D Cubism.
- **Anti-reference** (advertised feature unfinished / unsupported): Spriter Pro 1.x mesh deformation.

Each section below covers: (a) mesh creation flow, (b) bind / weight flow, (c) strengths, (d) weaknesses / community pain, (e) source URLs. Patterns synthesized into the matrix at the end.

### Spine (Esoteric Software)

**Mesh creation flow.** Each Region attachment ships rigid; toggling a `Mesh` checkbox in the tree converts it into a 4-corner mesh and opens the Mesh Tools view. Three coexisting creation paths: **Create** (click vertices, drag edges manually), **New vertices** (hull-perimeter mode), and two automated helpers - **Generate** (iterative: each press "adds new vertices to the mesh at positions that will benefit deformation the most" - the user densifies progressively rather than picking a density slider) and **Trace** (the full automesh - builds the concave hull from image alpha with knobs for `Detail`, `Concavity`, `Refinement` time-budget, `Alpha threshold`, `Padding`). Documented hard limit: "meshes can be concave but cannot have holes." Internal triangulation auto, overrideable by drawing orange edges manually. Preview toggles: Triangles, Dim, Isolate, Deformed. Exit via spacebar/escape/Edit Mesh button. Sources: [Mesh attachments](http://esotericsoftware.com/spine-meshes), [Mesh Tools view](http://esotericsoftware.com/spine-mesh-tools).

**Bind / weight flow.** Multi-select bones + mesh, click **Bind** to associate them, click **Auto** for initial weights. Spine is explicit that "this does not use simple distance between vertices and bones, Spine uses a sophisticated algorithm that considers the mesh topography to choose the best weights" but the actual algorithm name is never published - unclear from public docs whether heat-diffusion, geodesic, or proprietary ([Weights view](http://esotericsoftware.com/spine-weights)). Auto-weights can be re-run on a subset of vertices/bones, preserving manual edits elsewhere. The Weights view brush has three modes (**Add**, **Remove**, **Replace**) and three parameters (**Strength** max-weight cap, **Size**, **Feather** falloff %). A **Direct** mode types numeric values. **Lock** prevents specific bones' weights from changing while painting others. **Smooth** averages a vertex's weights with neighbours; **Prune** removes tiny weights and caps bones-per-vertex (run before export). Soft-selection in Mesh Tools (Size/Feather/Hull-only toggle) lets Rotate/Translate/Scale propagate to neighbour vertices with falloff.

**Strengths.** Two complementary automesh paths (iterative `Generate` for additive control, one-shot `Trace` for hull-from-alpha). Clean brush-intent separation (Add / Remove / Replace) rather than overloading a single brush. `Lock` + partial-selection auto-weights enable robust mixed manual+auto workflows. `Prune` formalises the export-time bones-per-vertex limit. Preview toggles (Deformed / Triangles / Dim / Isolate) cover the most common ambiguity.

**Weaknesses / community pain.** No documented mirror-weights feature; community asking for it since 2018 ([weight painting improvements request](https://esotericsoftware.com/forum/d/15276-request-weight-painting-improvements), [could there be improvements for the Weight Painting?](https://esotericsoftware.com/forum/d/13441-could-there-be-improvements-for-the-weight-painting)). Pen tablet pressure mapping not mentioned in official docs - unclear. Auto-weight algorithm is a black box; users cannot tune topology heuristics, only re-run and repaint ([Weights and Bones workflow issues](https://en.esotericsoftware.com/forum/d/5050-weights-and-bones-workflow-issues)). Runtime mismatch: meshes that look correct in editor deform differently in some runtimes ([Defold issue 2324](https://github.com/defold/editor2-issues/issues/2324)). Hard topological limit: mesh hull cannot have holes - blocks cutout characters with interior alpha gaps.

**Sources.** [Mesh attachments](http://esotericsoftware.com/spine-meshes), [Weights view](http://esotericsoftware.com/spine-weights), [Mesh Tools view](http://esotericsoftware.com/spine-mesh-tools), [Mesh creation tips: vertex placement](https://esotericsoftware.com/blog/Mesh-creation-tips-vertex-placement), [Auto Mesh? forum thread](https://esotericsoftware.com/forum/d/5578-auto-mesh), [Some features Spine is actually missing](https://en.esotericsoftware.com/forum/d/28041-some-features-spine-is-actually-missing).

### DragonBones (open-source Spine alternative)

**Mesh creation flow.** Manual only. Convert image to mesh, then place vertices by hand. The official Skin Weights doc opens with "First you need to convert the image to mesh and add mesh points" ([Skin Weights](https://docs.egret.com/dragonbones/en/docs/dbPro/advancedFeatures/skinWeights)). To enter edit mode, select the mesh and tick "Open Edit" on the property panel. No alpha-trace automesh; no density slider; no alpha threshold equivalent. The 5.2 release notes call out optimized grid editing + deform-mode mesh editing, implying earlier versions were rougher ([What's New 5.2](http://blog.dragonbones.com/en/release/whats-new-in-dragonbones-pro-5-2.html)).

**Bind / weight flow.** Two-click gesture: in mesh-edit mode click **Bind Bone** and then click the bones to bind. After binding, right-click on blank space and "it will auto calculate the weight assignment based on bone and mesh's relative position" - effectively distance-based proximity, not topology-aware. Per-vertex numeric editing via property-panel sliders. Visual editing via the Weight Tool's pie-chart-per-vertex (slices colour-coded to bones; drag up/down to change the active bone's slice). A **Smooth** button averages with neighbours. Mirror, lock, feather, pen-tablet pressure, dedicated brush size/strength/falloff - unclear from public docs.

**Strengths.** Free / open-source license (hard differentiator vs Spine paid model). The bind gesture (select bones, right-click blank) is fast for simple rigs. Pie-chart per-vertex visualisation is a clearer "what's bound here?" affordance than a single-bone heatmap. 5.2 added in-deform-mode mesh editing.

**Weaknesses / community pain.** No automesh - every vertex placed manually. Auto-weights is just distance heuristic, less sophisticated than Spine. Runtime fragmentation: Phaser doesn't support meshes ([phaser #5371](https://github.com/photonstorm/phaser/issues/5371)); GameMaker stuck on 3.4.02 runtime ([GameMaker thread](https://forum.gamemaker.io/index.php?threads/dragonbones-support.42233/)). Editor stability: "Import many assets constantly crash DragonBones" ([Starling forum](https://forum.starling-framework.org/d/19850-import-many-assets-constantly-crash-dragonbones)). Older-version file format breaks across versions ([Godot integration crash](https://github.com/sanja-sa/gddragonbones/issues/4)). NightQuestGames review: "AutoMesh allows you to automatically generate a mesh around an image, but unfortunately, the resulting meshes are not accurate enough" ([NightQuestGames review](https://www.nightquestgames.com/dragonbones-animation-the-ultimate-animation-software-for-beginners/)).

**Sources.** [Skin Weights](https://docs.egret.com/dragonbones/en/docs/dbPro/advancedFeatures/skinWeights), [What's New 5.2](http://blog.dragonbones.com/en/release/whats-new-in-dragonbones-pro-5-2.html), [Tutorial 3 - Meshing images](https://www.youtube.com/watch?v=HJNJ0d1fRxE), [Tutorial 4 - Editing Mesh Weights](https://www.youtube.com/watch?v=8kQBre6_vd8).

### Spriter Pro (anti-reference)

**Anti-reference: mesh deformation is effectively unsupported in Spriter Pro 1.x.** Deliberate inclusion - the Proscenio team can use Spriter Pro as a "what happens when you ship a 2D rigger without mesh deformation" case study. A hidden "skin mode (experimental)" appears in a dropdown only when OpenGL is enabled; BrashMonkey staff have stated repeatedly on the forums and Steam community that "skin mode was never finished, has some bugs, and is not supported by any run-time API or plug-in" ([Steam: Does not available mesh deformation?](https://steamcommunity.com/app/332360/discussions/0/3288067088086478830/), [BrashMonkey forum: How to Use Mesh and FFD in Spriter](https://brashmonkey.com/forum/index.php?/topic/4116-how-to-use-mesh-and-ffd-in-spriter/)). Officially described as "place-holder/proof of concept", useful only when exporting finished animations as full-frame images / GIFs.

Spriter 2 (in alpha/beta as of 2026, currently Beta 2026.04.26) is the planned replacement and explicitly advertises "many forms of mesh deformation, curve based and bone based hierarchies" plus a new **attractor** deformation system "to allow deformation with arbitrary configurations of deformation handles" ([Spriter 2 alpha 0.9.5](https://x.com/Spriter2D/status/1777112939473895715)). BrashMonkey disabled "multi-bone mesh attachments and mesh deformers (except contour mesh)" in a December 2024 update while reworking the animation paradigm. Production-ready mesh+weight workflow is still moving target.

**Implication for SPEC 013:** the lesson is "don't ship a mesh deformation feature that doesn't actually work end-to-end." Better to defer than half-ship. Spriter's nearly-decade-long "mesh is coming soon" reputation is a cautionary tale.

**Sources.** [Steam discussion](https://steamcommunity.com/app/332360/discussions/0/3288067088086478830/), [Free-Form Deformation? Steam](https://steamcommunity.com/app/332360/discussions/0/351660338690641338/), [BrashMonkey: How to Use Mesh and FFD](https://brashmonkey.com/forum/index.php?/topic/4116-how-to-use-mesh-and-ffd-in-spriter/), [Where is the Mesh Deformation update?](https://brashmonkey.com/forum/index.php?/topic/5389-where-is-the-mesh-deformation-update/), [Spriter 2 product page](https://brashmonkey.com/).

### Live2D Cubism

**Paradigm overview.** Fully deformer-based, not bone-based. Two primitives: **Warp Deformer** (Bezier lattice / grid that bends what is inside) and **Rotation Deformer** (pivot that rotates / scales / offsets children). Geometry held in **ArtMeshes**; deformers act on ArtMeshes by being their *parents* in a hierarchy, never by being "attached" to specific vertices. No per-vertex weights in the bone-and-skin sense - influence is purely a function of parent hierarchy. A single ArtMesh can only have one direct deformer parent, but deformers nest arbitrarily.

**Mesh / topology creation flow.** Every imported PSD layer becomes an ArtMesh. Two paths: **Automatic Mesh Generation** (density via point spacing, repeat density, boundary margin - Cubism tessellates the alpha shape) or **Edit Mesh Manually** (click vertices and edges one by one). Docs explicitly recommend manual editing for high-deformation parts (eyelashes, mouth, eyelids) because auto density rarely yields the loop topology needed for clean blink/lip-sync. Mesh density and deformer choice are independent - heavier meshes only matter for the ArtMesh holding the geometry, not for the deformer lattice (which has its own `Number of conversion divisions`, default 5x5, with a warning that larger grids are expensive). Source: [mesh-edit](https://docs.live2d.com/en/cubism-editor-manual/mesh-edit/).

**Bind / weight / skin flow.** "Binding" is **re-parenting** in the Deformer palette - not weight painting. Three higher-level affordances bolt on:

- **Skinning** (`Modeling > Skinning`): the closest thing to traditional skinning. When you place several rotation deformers along an ArtMesh (e.g. a tail or hair strand) and run Skinning, Cubism automatically slices the ArtMesh between each pair of rotation deformers, "glues" the seams, and auto-generates angle parameters for each rotation deformer (default range -45..+45). This is the workflow most analogous to a bone chain. The **Deform Path** flow is recommended because parameters and ranges are produced for you ([Skinning doc](https://docs.live2d.com/en/cubism-editor-manual/skinning/)).
- **Glue** binds overlapping vertices of two ArtMeshes with a weight slider that biases which side dominates - closest Cubism feature to per-vertex weights, used for seams (neck/body, sleeve/arm) ([Glue doc](https://docs.live2d.com/en/cubism-editor-manual/glue/)).
- **Auto Generation of Deformer** estimates a full human-figure deformer rig from ArtMesh placement, giving a one-click starting hierarchy ([Auto Generation doc](https://docs.live2d.com/en/cubism-editor-manual/auto-generation-of-deformer/)).

**Iteration strength.** Editing an ArtMesh after binding does not break the rig. **Restore Deformer Shape** (`Revert to original`) snapshots the deformer at creation and at each key, so accidental drift can be undone ([Restore Deformer Shape doc](https://docs.live2d.com/en/cubism-editor-manual/restore-deformer-shape/)). Cubism 5.2 adds a setting to disable the foot-gun where double-click in Deform Brush used to drop you into Mesh Edit.

**Inspiration for Proscenio.** (a) **One-shot Skinning operator on top of a bone chain** - in Proscenio, `Skin to chain` could (i) cut/segment the auto-generated mesh between consecutive bones, (ii) seed weights with smooth falloff at each cut, (iii) wire up bone-rotation drivers in one click. (b) **Snapshot-restore for the deformable surface** mirroring `Restore Deformer Shape`: cache rest-state mesh + weights when binding so the user can re-tessellate mid-rig without losing manual touch-ups - this is the answer to Blender's "remesh destroys weights" problem.

### Moho (Lost Marble / Smith Micro)

**Paradigm overview.** Bone-based but with a distinctive twist: bones live in a **Bone Layer** and act on whatever child layers (vector or image) you drop inside it. Each bone exposes a **Strength** (region of influence) instead of demanding per-vertex weights up front. **Smart Bones** add another layer: a bone whose rotation drives a recorded action curve, so deformation is partly authored by keying *the rig itself* rather than per-vertex skinning. Net feel: "bones + radial influence + dial-driven correctives" - hybrid of Spine bones and a driver-shape system.

**Mesh / topology creation flow.** Moho's "mesh" is the vector artwork itself - points and segments drawn (or imported) on a vector layer. No separate tessellation step; the points you draw are the points the bones will move. Image layers can be deformed when placed inside a bone layer (treated as textured quad / mesh). Density is implicit in how detailed you draw - recommended ergonomic is to add anchor points only where you need a hinge or a bulge to read on screen.

**Bind / weight / skin flow.** Three coexisting modes, switchable in `Layer Settings > Bones`:

- **Flexible binding** (default): every bone influences every point with distance falloff. Zero setup but produces the famous "rubbery" warping if bones are too close.
- **Region binding**: each bone has a circular/elliptical **strength region**, edited interactively with the **Bone Strength** tool by dragging side-to-side on the bone. A point only moves under bones whose region contains it; overlapping regions blend. **Per-bone radius, not per-vertex weight** - authoring weight for a whole limb is one drag.
- **Bind Points** + **Bind Layer** (since Moho 5.0, less recommended): explicit lasso-and-bind hard assignment.

Smart Bones layer on top of any of these. Designate a bone as smart, create a **Smart Bone Action** (e.g. "elbow bend 0 to 90"), animate any rig change inside that action - vector point offsets, sub-bone rotations, switch-layer swaps. When the parent bone later rotates, Moho interpolates the action proportionally. This is how clean joints, face turns and corrective bulges are authored without painting weights at all.

**Inspiration for Proscenio.** (a) **Region/strength painting as the default authoring metaphor** before per-vertex weights: Proscenio could expose a per-bone elliptical/capsule "influence region" widget (drag a handle along the bone to grow/shrink radius) that *generates* the initial weight map procedurally, falling back to weight paint only for fix-ups. Collapses "I need to weight 60 vertices" into "drag two handles." (b) **Corrective-action drivers analogous to Smart Bones**: even a thin version (per-bone shape key driven by bone rotation, baked through `update_tag`) would meaningfully reduce joint-cleanup iteration cost. (b) is Wave 13.2 / 14 material.

**Sources.** [Bone Tools manual](https://www.lostmarble.com/moho/manual/bone_tools.html), [Moho features](https://moho.lostmarble.com/pages/features), [Walkthrough: Moho binding methods](https://lesterbanks.com/2016/11/walkthrough-moho-binding-methods/), [Flexi binding method](https://lesterbanks.com/2016/11/working-flexi-binding-method-moho/), [Layer / point binding](https://lesterbanks.com/2019/04/layer-binding-and-point-binding-in-moho-pro/), [Smart Bone Actions](https://www.animestudiotutor.com/bones/smart_bone_actions_in_moho_anime_studio/).

### Toon Boom Harmony

**Paradigm overview.** Most "professional pipeline" of the three. Explicitly hybrid: **three deformer node types** that mix in one rig - **Bone** (rigid segments with articulations, for limbs), **Curve** (Bezier spline chain with manipulable handles, for hair/tails/facial features without joints), and **Envelope** (closed contour around the drawing whose points and tangents bend the whole shape). These deformers act on the drawing's *outlines* by default; a separate **Weighted Deform** node converts any of them into full-texture (interior) deformation - the closest Harmony comes to a mesh-deformer skin.

**Mesh / topology creation flow.** Drawings come in as vectors or bitmaps and have no explicit mesh until a deformation is added. The deformation chain itself is the topology: pick the Rigging tool, click-drag along a body part, and Harmony lays down deformer joints (bones, curve points, or envelope points) in sequence, auto-wiring them as a chain in Node view. Envelope deformations let you place points freely around the silhouette to define the deformable boundary. For interior deformation, connect chain(s) and (optionally) pegs into a **Weighted Deform** node, which acts as a blender of regions defined by each source.

**Bind / weight / skin flow.** Binding is largely *implicit* and chain-driven rather than weight-painted:

- Bone and Curve chains: every joint has a **Bias** / influence range along the chain; per-joint zones interpolate which joint owns which portion. No per-vertex weight paint in the Blender sense; the deformer chain itself carries falloff metadata.
- **Weighted Deform**: connect deformation chains, pegs, and free deformation points to the same node; each source contributes a region of influence blended automatically. Docs frame this as "creating a blended deformation from the regions defined by multiple sources" - the user authors *regions*, not vertex weights.
- **Auto-Patch nodes** solve the classic 2D "joint hole" problem at articulations (elbow, knee, shoulder): once chain is rigged, drop an Auto-Patch node on each joint and it automatically masks/patches the seam between two body parts as the joint bends, with no parameters to tune. **Conceptually a free auto-weighting of the joint cover.**

**Inspiration for Proscenio.** (a) **"Auto-Patch at articulations" as a first-class operator**: a one-click joint-cover that, given two child meshes sharing a parent bone, generates the seam geometry / weight blend that hides the inner-elbow hole - users get clean joints without ever opening weight paint. (b) **Region-blending mindset for multi-chain weights**: let the addon expose multiple weight "sources" (per-bone region, per-stroke vertex group, free-form lattice handle) and combine them with explicit blend weights. (a) is Wave 13.2; (b) is Wave 14+.

**Sources.** [About deformation](https://docs.toonboom.com/help/harmony-22/premium/getting-started/deformation.html), [Weighted Deformations](https://docs.toonboom.com/help/harmony-22/premium/deformation/about-weighted-deformations.html), [Auto-Patch articulation](https://docs.toonboom.com/help/harmony-22/premium/rigging/about-auto-patch-articulation.html), [Rigging tool properties](https://docs.toonboom.com/help/harmony-22/premium/reference/tool-properties/rigging-tool-properties.html), [Auto-Patch activity tutorial](https://learn.toonboom.com/modules/art-layers-and-auto-patches/topic/activity-1-rigging-with-auto-patch-nodes).

### Adobe Animate

**Mesh creation flow.** Two overlapping rigging tools: legacy **Bone tool** (works on shapes and linked symbol chains) and modern **Asset Warp tool** (introduced as part of "Modern Rigging", recommended path). With Asset Warp the artist clicks the sprite to drop a first **joint**; each subsequent click drops another joint, and Animate auto-generates a **triangulated mesh** between them and a bone segment between the two latest joints. No explicit "mesh creation" step - the mesh is implicit and regenerated as joints are added. Mesh density exposed as a single **Mesh density slider** in Properties: higher = smoother deformation, lower = better performance, Animate auto-computes a default. For the legacy Bone tool on raw shapes, the shape's vector control points become the deformable "mesh"; bones are dropped along the shape and Animate binds each control point to the nearest bone.

**Auto-weight algorithms + UX.** Animate does **not expose a heat-diffusion-style weight solver**. Binding is implicit and proximity-based:

- Legacy Bone tool: each shape control point is auto-bound to the nearest bone at creation time. Points bound to one bone show as **squares**, points bound to several show as **triangles**.
- Asset Warp tool: weights derive from triangulated mesh + bone topology. **Hard bones** (default) act as rigid transforms on their region; **Soft bones** smooth influence falloff across neighbouring mesh triangles. Switching **Bone Type** in Warp Options changes behaviour and Animate propagates the change to all keyframes automatically.

Because binding is geometric/topological, no equivalent of the Blender "Bone Heat Weighting: failed to find solution" error. Trade-off: artist has **little numeric control** - no per-vertex weight values, no normalization, no vertex group panel - only the soft/hard toggle, mesh density, and per-joint **Freeze Joint** flag.

**Manual weight brush UX.** **No brush-based weight painting in Animate.** Manual influence editing limited to the **Bind tool** (legacy bones): select a bone to highlight its bound control points in yellow (selected bone in red), Shift-click to add a control point to a bone, Ctrl-click to remove it. A control point can bind to multiple bones, but weights are **binary / nearest-neighbour, not continuous floats**. No mirror, no smooth/blur, no gradient, no falloff curve. The community calls this out repeatedly: precision-rigging asks get answered with "add more joints" or "raise mesh density" rather than "paint weights" ([Asset Warp precision community thread](https://community.adobe.com/t5/animate-discussions/asset-warp-tool-and-modern-rigging-precision/td-p/14353673)).

**Subdivision / under-bone density.** Single global **Mesh density slider** controls triangulation for the entire warped asset. No localized "add more triangles around this joint" control - artist either raises the global slider (perf cost everywhere) or adds more joints in that region (locally densifies the triangulation). Coarser than Spine's per-region mesh editing.

**Strengths.** Zero-friction binding: drop joints, deform immediately. Soft vs Hard bone toggle covers 80% of cases without numeric weights. Pose keyframing integrates natively with Animate timeline. Freeze Joint is a clean primitive.

**Weaknesses / community pain.** No painted weights, no vertex-group concept, no continuous influence editing. Global-only mesh density; no local subdivision. Bind tool hidden, legacy, undocumented for Asset Warp flow. Mesh density slider can silently break existing poses. No round-trip export to other engines. Asset Warp behaving erratically in Animate 2025 ([thread](https://community.adobe.com/t5/animate-discussions/asset-warp-tool-behaving-strangely-in-animate-2025/td-p/15402541)). Bone-length adjustments shift attached mesh ([thread](https://community.adobe.com/t5/animate-discussions/new-asset-warp-tool-bone-length/td-p/12836442)). Meta-complaint: "good enough for marketing animation, not precise enough for character rigging" - users who outgrow it move to Spine or Live2D.

**Inspiration for Proscenio.** The **soft/hard bone toggle** is a clean abstraction worth borrowing - gives smoothing without exposing per-vertex weights. Default Proscenio binding mode could ship "soft" (proximity falloff seed) and let users flip to "hard" (1.0 weight to single nearest bone) per-bone, parallel to Animate's mental model.

**Sources.** [Character rigging in Animate](https://helpx.adobe.com/animate/using/character-rigging-in-animate.html), [Bone tool animation](https://helpx.adobe.com/animate/using/bone-tool-animation.html), [Asset Warp tool](https://helpx.adobe.com/animate/how-to/asset-warp.html), [Animating with Asset Warp](https://helpx.adobe.com/animate/how-to/animate-with-asset-warp.html), [Mysteries of the Bone Tool](https://blog.adobe.com/en/publish/2016/05/18/mysteries-of-the-bone-tool), [Using the Asset Warp tool - Peachpit](https://www.peachpit.com/articles/article.aspx?p=3172423&seqNum=3).

### Blender native (no addons - the baseline Proscenio inherits)

**Mesh creation / topology flow.** For 2D-cutout work the baseline is a **plane** (often subdivided) or UV-mapped sprite plane; the artist plans to map a texture, then parents the plane to an Armature. **No native "auto-mesh from sprite alpha"** - the artist creates topology by hand (Loop Cut, Subdivide, Knife) or uses a Subdivision Surface modifier above the Armature modifier. Resolution fixed at parenting time; later changes invalidate existing weight paints in modified regions.

**Auto-weight algorithms + UX.** Select mesh, Shift-select armature, **`Ctrl+P` -> Armature Deform -> With Automatic Weights**. Other menu options: **With Envelope Weights** (capsule-around-bone influence based on each bone's envelope radius - easy to set up but imprecise and overlap-prone) and **With Empty Groups** (creates one empty vertex group per deforming bone, weights all zero - used for manual painting from scratch or weight transfer).

"Automatic Weights" runs the **bone heat** algorithm: each bone treated as a heat source, weights computed by surface heat diffusion (implementation is surface, not volumetric; Blender devs and Voxel Heat Diffuse third-party addons critique this choice). When it fails:

> **Bone Heat Weighting: failed to find solution for one or more bones**

Documented causes ([T45493](https://developer.blender.org/T45493), [T51250](https://developer.blender.org/T51250), [#127345](https://projects.blender.org/blender/blender/issues/127345)): (a) **non-manifold geometry** (loose vertices, interior faces, free edges); (b) connected components / islands not visible to any bone (the matrix becomes non-invertible and **the whole solve fails for all bones**, not just the orphan island); (c) duplicated/overlapping vertices; (d) bones embedded inside the mesh or completely outside it; (e) very thin, planar, or self-intersecting geometry - **exactly the topology of 2D cutout sprite planes**. Workarounds: `Mesh > Clean Up > Merge by Distance`, Recalculate Normals, delete loose, ensure every bone tip lies near (but inside the silhouette of) the deforming mesh, or fall back to **With Empty Groups** + manual painting.

Widely described in community threads as "fragile" - exactly the audience pain Proscenio targets.

**Manual weight brush UX.** Enter **Weight Paint mode** (mode dropdown, or Ctrl+Tab). Mesh recoloured by the active vertex group's weights (blue=0, green=0.5, red=1). Shift-click bones in the armature (visible via Armature modifier) to switch active vertex group, or pick from Vertex Groups panel.

**Brush settings** (Tool sidebar / N-panel): Radius, Strength, Weight (target 0..1), Falloff curve preset (Smooth, Sphere, Root, Sharp, Linear, Constant) + custom curve editor. **Blend modes**: Mix, Add, Subtract, Multiply, Blur, Lighten, Darken, Average. Add caps at 1.0, Subtract floors at 0.0, **Blur ignores Weight Value and just smooths neighbours** (notoriously misbehaves on thin/planar meshes, sending random vertices to unintended bones).

**Options (Tool > Options panel)**: **Auto Normalize**, **Multi-Paint**, **Vertex Group Lock**, **X Mirror** (only mirrors weights across the X axis and only if rest pose is perfectly symmetrical - known broken in combinations with Mirror modifier, [T72158](https://developer.blender.org/T72158), [T71213](https://developer.blender.org/T71213)). **Mirror brush operator** mirrors the active group's existing weights to the opposite side.

**Gradient tool**: `Alt-LMB drag` = linear gradient, `Ctrl-Alt-LMB drag` = radial gradient. **Gradient ignores X-Axis Symmetry option** ([T99668](https://developer.blender.org/T99668)).

**Weight Tools menu**: Normalize All, Normalize, Mirror, Invert, Clean, Quantize, Levels, Smooth, Transfer Weights, plus **Data Transfer modifier** for cross-object weight transfer. Smart bone naming (vertex groups auto-named from bones at parenting).

**Pen tablet**: pressure sensitivity drives Strength and/or Radius via the pen icons next to each slider ([T73377](https://developer.blender.org/T73377) documents driver-specific breakage). No semantic per-stroke undo for accidental Blur edits other than Ctrl+Z. Painting through the mesh requires toggling **Front Faces Only** off and/or enabling **2D Falloff** - without this, the back face of a sprite plane is unreachable from the front. The BlenderNation tutorial covering this fix is itself the canonical reference ([Paint through mesh tutorial](https://www.blendernation.com/2021/01/24/how-to-paint-through-the-mesh-in-weight-paint-mode-blender-2-83-2-91-2-92-2-93/)).

**Subdivision / under-bone density.** No native "auto-subdivide under deformer" feature. Resolution authored at mesh-creation time or via a **Subdivision Surface modifier** placed **after** the Armature modifier. For 2D planes rarely the right answer: subsurf is Catmull-Clark and pulls silhouettes inward. Practical workaround: manual Loop Cut / Subdivide in Edit Mode at joint regions. **No UI affordance "densify mesh where a bone passes through."**

**Strengths.** Full continuous-float weights, vertex group lock, normalization. Powerful brush stack (Add/Sub/Multiply/Blur/Smooth + curve falloff + gradient tool). Data Transfer modifier enables rig-swap workflows. Mature pen-tablet pressure pipeline (when drivers cooperate). Open / scriptable (bpy access to every weight, every group).

**Weaknesses (specific to 2D-cutout use).**

- Bone heat solver fragile and fails opaquely on exact topologies 2D rigging uses (planes, thin geo, islands).
- Blur brush corrupts weights on thin meshes (reads through plane, pulls weights from back face).
- X-Mirror does not work as expected with Mirror modifier + Armature combos.
- Auto-weights overshoot regions (nose/mouth weighted by neck bone).
- No "paint through" by default - artists must rediscover Front Faces Only / 2D Falloff every project.
- Discoverability: vertex group locking, Auto Normalize, falloff curve, gradient tool live in different panels.
- Normalization confusion: weights look correct in paint mode but fail at deform time because Auto Normalize was off.
- Blur+Smudge currently crash on undo ([#149138](https://projects.blender.org/blender/blender/issues/149138)).

Summary across community threads: Blender weight paint is powerful but assumes the artist already knows 3D character workflow. Applied to a flat 2D-cutout pipeline, every default is wrong (occlude geometry on, no subsurf, X-Mirror conditional, bone heat brittle on planes). This is precisely the audience SPEC 013 targets.

**Sources.** [Armature Deform Parent](https://docs.blender.org/manual/en/latest/animation/armatures/skinning/parenting.html), [Weight Paint introduction](https://docs.blender.org/manual/en/latest/sculpt_paint/weight_paint/index.html), [Weight Paint Brushes](https://docs.blender.org/manual/en/latest/sculpt_paint/weight_paint/brushes.html), [Weight Paint Tools (Gradient)](https://docs.blender.org/manual/en/latest/sculpt_paint/weight_paint/tools.html), [Weight Paint Options](https://docs.blender.org/manual/en/latest/sculpt_paint/weight_paint/tool_settings/options.html), [Data Transfer Modifier](https://docs.blender.org/manual/en/latest/modeling/modifiers/modify/data_transfer.html), [Volumetric Heat Diffusion blog](https://bronsonzgeb.com/index.php/2021/06/26/volumetric-heat-diffusion-for-automatic-mesh-skinning/), [Weight painting, why so painful?](https://blenderartists.org/t/weight-painting-why-so-painful/683410), [Bone Heat failed - BlenderArtists](https://blenderartists.org/t/bone-heat-weighting-failed-to-find-solution-for-one-or-more-bones/701412), [Big issue with rigging and weight paint](https://blenderartists.org/t/big-issue-with-rigging-and-weight-paint/1176591).

### COA Tools 2 (direct prior art, GPL Blender addon)

Reference: [Aodaruma/coa_tools2](https://github.com/Aodaruma/coa_tools2), default branch `master`, GPL-3.0, ~73 stars, 20 open issues, last updated 2026-04-20. Direct successor of `ndee85/coa_tools` (original by Andreas Esau). Aodaruma fork targets Blender 3.4+ (patched up to 5.1) - the only actively maintained 2D-cutout-rigging addon in the Blender ecosystem.

**Automesh.** Source: `coa_tools2/operators/automesh.py` (operator `COATOOLS2_OT_AutomeshFromTexture`, `bl_idname coa_tools2.automesh_from_texture`).

How it works:

1. Reads the active mesh's `TEX_IMAGE` node, grabs the absolute filepath, reads the PNG with `cv2.imread(..., IMREAD_UNCHANGED)`.
2. Extracts the alpha channel, downsamples by `resolution` (default 0.25), adds 50px padding border, thresholds with `cv2.threshold(..., 127, 255, BINARY)`, optionally dilates/erodes by `margin`, then `cv2.findContours(..., RETR_TREE, CHAIN_APPROX_TC89_KCOS)`.
3. Generates **two** contours per sprite: an outer contour (positive margin = dilate) and an inner contour (negative margin = erode). Each contour is "relaxed" via 3 iterations of Laplacian smoothing + arc-length resampling.
4. Converts contour points to bmesh verts in plane `(x, 0, -y)` scaled by `1/resolution/100`. Outer + inner edges get `bmesh.ops.triangle_fill` (annulus triangulation) so the sprite gets a ring of dense edge loops near silhouette + interior coverage.
5. Re-running automesh **only removes verts not in the `coa_base_sprite` vertex group** - the original quad base sprite is preserved (the addon's data-preservation anchor).
6. Hides base sprite quad afterwards via `obj.data.coa_tools2.hide_base_sprite = True`.

Knobs (operator redo panel): `resolution` (0.01-1.0, default 0.25), `threshold` (0-255, default 127), `margin` (0.01-100, default 5), `is_create_faces` (default False).

**External deps:** requires `opencv-python` (cv2) + numpy installed into Blender's Python via the addon's installer. On missing deps a popup nags the user. Issues [#94](https://github.com/Aodaruma/coa_tools2/issues/94) + [#107](https://github.com/Aodaruma/coa_tools2/issues/107) confirm this is a recurring friction point - reporter's ISP blocked PyPI, fix required manually copying cv2 from another app which broke numpy ABI.

**UX notes:** the operator is `REGISTER, UNDO` so changes in the redo panel re-run it. After [PR #113](https://github.com/Aodaruma/coa_tools2/pull/113) (merged to develop 2026-04-04, fixes [#108](https://github.com/Aodaruma/coa_tools2/issues/108)), running with the same parameters preserves the previous mesh if the new contour is empty, and stale geometry is removed before regeneration.

**Weight paint modal wrapper.** Source: `coa_tools2/operators/edit_weights.py` (`COATOOLS2_OT_EditWeights`, `bl_idname coa_tools2.edit_weights`).

Helpers beyond Blender native:

1. **Modal "Edit Weights" wrapper** - one-button entry/exit. On invoke: forces `armature.hide_viewport = False`, hides all non-deform bones, un-hides deform bones, switches armature to POSE, switches sprite to WEIGHT_PAINT, enables local view, sets `use_auto_normalize = True`, zooms via `view3d.view_selected`, enables `overlay.show_paint_wire`, selects the first vertex group matching a bone name.
2. **GPU draw overlay** - custom `draw_handler` (`draw_callback_px`) draws a 6px filled disc per vertex coloured by weight via a 6-stop colorband (red->orange->yellow-green->green->cyan->blue), with alpha 0 for unweighted verts. **Louder than Blender's native gradient** - signature COA visual that makes light weights visible (Blender native washes them out under 0.15).
3. **Auto armature modifier** - if the sprite has no Armature modifier, one is added pointing at the rig.
4. **Restores prior state on exit** - bone collection visibility, unified-paint settings, selection, active object, viewport shading.
5. **Modal auto-exit** - if the user leaves WEIGHT_PAINT mode or local view by any means, the modal calls `exit_edit_mode` and restores state.

What it does **not** offer: no built-in mirror, no symmetry presets, no per-bone fill-to-1, no weight transfer between sprites ([issue #18](https://github.com/Aodaruma/coa_tools2/issues/18) + [#73](https://github.com/Aodaruma/coa_tools2/issues/73) both request these and are open since 2023/2024), no auto-mask by alpha, no smooth-falloff brush preset.

**Bind workflow.** Source: `coa_tools2/operators/edit_armature.py` + `coa_tools2/functions.py`.

`functions.set_weights` (functions.py:243-304) - the workhorse. For each selected edit-bone:

- Removes the mesh's existing vertex groups matching bone names (full replace, not merge).
- Marks ONLY the selected bones as `use_deform = True`, all others `use_deform = False` temporarily.
- **Snaps the head/tail Y-coord to 0** so 2D distance math works (the rig lives on Z=0 plane).
- Calls `bpy.ops.object.parent_set(type="ARMATURE_AUTO")` - **Blender's "Automatic Weights" parenting is the entire bind algorithm**.
- Restores original tail/head Y and `use_deform` flags.

**This is the screenshot-confirmed bug C from the user's Discord context.** A 3-bone arm + hand sprite -> click Edit Weights -> Blender 5.1 traceback `bone.select = False` at edit_weights.py:86 (Blender 5.1 removed `Bone.select`). Combined with the AUTOMATIC_WEIGHTS bind algorithm, even when the modal works, the hand sprite often ends up entirely weighted to the forearm bone because the hand bone may not overlap the hand sprite verts in 3D space at all. Fixed in [PR #114](https://github.com/Aodaruma/coa_tools2/pull/114) (Blender API compat), but the deeper bind-quality issue is unaddressed.

**Draw 2D Polygon tool.** Source: `coa_tools2/operators/edit_mesh.py` (`COATOOLS2_TO_DrawPolygon` WorkSpaceTool, `COATOOLS2_OT_DrawContour` modal at line 719).

LMB press = start contour; LMB drag = lay a vert every `scene.coa_tools2.distance` units along the drag. ALT+drag = delete. SHIFT+hover edge = eyedropper picks stroke distance. CTRL = restore_edit_local_view (suspends drawing). **ESC = deselect verts only (line 1571) - does NOT exit the tool**. Exit only via TAB (line 1581).

**This is the screenshot-confirmed bug B (pen tablet stroke continues after Esc).** Root cause: `self.mouse_press = False` is only set when `event.value == "RELEASE" and event.type in {"MOUSEMOVE","LEFTMOUSE"}` (lines 1493-1496). Wacom/XP-Pen drivers under Windows Ink emit `WINDOW_DEACTIVATE` or no MOUSEMOVE-with-RELEASE when the pen lifts, so `mouse_press` stays True until the next `LEFTMOUSE+RELEASE`, and the modal keeps adding verts. **No tablet/pen pressure handling wired at all** (`grep -E 'TABLET|PEN|pressure|tilt'` returns zero hits in the operator). No dedicated issue exists in the COA tracker for this bug - unreported but confirmed-reproducible via code inspection.

**Known bugs (top 5 relevant to SPEC 013).**

| # | Status | Title | Summary |
| --- | --- | --- | --- |
| [108](https://github.com/Aodaruma/coa_tools2/issues/108) | closed (PR #113 on develop) | Automesh: changing Resolution right after generation can make sprite disappear | **Screenshot bug A.** Sprite vanishes; re-run brings it back. Contour-cache invalidation timing. |
| [109](https://github.com/Aodaruma/coa_tools2/issues/109) | closed (PR #114 on develop) | Edit Weights: `Bone.select` no attribute on Blender 5.1 | **Screenshot bug C.** Modal label switches but mode stays Object. Blender 5.1 API breakage. |
| [94](https://github.com/Aodaruma/coa_tools2/issues/94) | open | Automesh error Requires Cv2 and numpy | Adoption blocker. Aodaruma's deliberate not-auto-install to avoid polluting Blender Python env. |
| [73](https://github.com/Aodaruma/coa_tools2/issues/73) | open | Non-destructive Weight Transfer Between Layers | Power user request: share weights across layered sprites (Live2D-style line/colour/shadow split). |
| [18](https://github.com/Aodaruma/coa_tools2/issues/18) | open | Add operator to copy/link mesh/weight/shapekey to another sprites | Foundational request open since project inception. |

**What Proscenio should LIFT from COA Tools 2:**

1. **One-button modal wrapper for weight paint with auto-rollback.** The pattern of "store viewport state + bone visibility + unified paint settings -> enter WEIGHT_PAINT + filter to deform bones only + auto-select matching vertex group -> on exit restore everything" is the single biggest ergonomic win. Compatibility shim pattern (`set_data_bone_selected` probing `select_set` / `select` / `select_head` / `select_tail`) is also the right approach for surviving Blender API drift.
2. **GPU-overlay weight visualisation per vertex.** Custom `draw_callback_px` drawing filled colour-coded discs per vertex weighted by the active group, alpha 0 for zero-weight. Makes light weights visible. Lift verbatim, possibly add per-bone toggle.
3. **Automesh "two-contour" pattern (outer dilate + inner erode + triangle_fill annulus).** Single contour creates ugly silhouette triangles; two contours + `triangle_fill` give a clean ring of edge loops that deforms predictably. Even without OpenCV, the topology shape (annulus + interior fill) is the right target.
4. **`coa_base_sprite` vertex group as data-preservation anchor.** Re-running automesh removes only verts NOT in `coa_base_sprite`. Solves "user lost their hand-tweaked UVs" elegantly. Adopt the same vertex-group-as-anchor pattern in Proscenio.

**What Proscenio should AVOID / FIX vs COA Tools 2:**

1. **Don't depend on OpenCV/numpy at install time.** Issues #94 and #107 prove this is the addon's biggest adoption blocker. Use Blender-native `bpy.types.Image.pixels` buffer + pure-Python contour walker (Moore neighbour or marching squares on alpha channel). Issue [#6](https://github.com/Aodaruma/coa_tools2/issues/6) commenter `tozpeak` already argued this approach.
2. **Don't make ESC a no-op inside the draw modal.** Root cause of screenshot bug B. Proscenio's draw-mesh modal must (a) treat ESC as both "release pending stroke" AND "exit modal", (b) handle `WINDOW_DEACTIVATE`, (c) detect tablet release via `event.pressure == 0` + timer-based fallback.
3. **Don't hide non-deform bones globally and trust restore.** If the modal crashes, the user wakes up with half their rig hidden and no obvious way back. Use Blender's bone Collections (4.0+) visibility instead - per-view-layer, undo-stack-aware, restored automatically on Ctrl-Z.
4. **Don't rely on `parent_set(type="ARMATURE_AUTO")` as the bind algorithm without per-bone weight inspection.** This is the root of screenshot complaint "hand sprite not binding despite simple setup." Proscenio should (a) do its own planar distance-to-bone-segment with falloff, (b) require bone-bbox overlap before auto-weighting, (c) offer an explicit "1.0 weight to active bone" fallback button.

**Sources.** [Aodaruma/coa_tools2 repo](https://github.com/Aodaruma/coa_tools2), [docs/overview](https://github.com/Aodaruma/coa_tools2/blob/master/docs/overview.md), [docs/specification](https://github.com/Aodaruma/coa_tools2/blob/master/docs/specification.md), [PR #113 stabilize automesh refresh](https://github.com/Aodaruma/coa_tools2/pull/113), [PR #114 Blender 5.1 bone API compat](https://github.com/Aodaruma/coa_tools2/pull/114), [PR #112 dep install hardening](https://github.com/Aodaruma/coa_tools2/pull/112), [COA Tools Discord](https://discord.gg/5vhZmCXczr), [Andreas Esau overview YouTube](https://www.youtube.com/watch?v=lRVnk1PMDTs), [Spine Pro vs COA Tools comparison](https://www.youtube.com/watch?v=wua9RwwjhYk), [Blender Artists COA outliner thread](https://blenderartists.org/t/coa-tools-outliner-import-mesh/1200436).

## Community pain themes

Synthesis of recurring complaints across BlenderArtists, Reddit (r/blender, r/animation, r/gamedev, r/2DAnimation), Blender Stack Exchange, Spine forums, Adobe Community, Toon Boom learn, and Cubism docs. Six themes ordered by frequency; "Implication for SPEC 013" closes each.

### 1. 2D Rigging Weight Paint Pain in Blender

Blender's weight paint mode was designed around 3D characters with closed manifolds and view-occluding faces. 2D cutout artists hit the friction immediately because a plane has a front and back face stacked at zero thickness; the **Front Faces Only** default silently breaks every brush stroke.

User signal: BlenderArtists [problem with weight painting 2D model](https://blenderartists.org/t/problem-with-weight-painting-2d-model/676824) - "automatic weight binding often requires subsequent manual weight painting to work properly," vertex groups bleed across overlapping layered planes. BlenderNation [paint through the mesh tutorial](https://www.blendernation.com/2021/01/24/how-to-paint-through-the-mesh-in-weight-paint-mode-blender-2-83-2-91-2-92-2-93/) explains "many users thought painting on back faces was broken" - the fix requires both unchecking Front Faces Only AND enabling 2D Falloff/Projected falloff, a non-obvious two-setting combo. Blender devtalk thread title is literally "[Painting through the mesh is not intuitive or user friendly](https://devtalk.blender.org/t/painting-through-the-mesh-is-not-intuitive-or-user-friendly/15231)". Tracked as [T58155](https://developer.blender.org/T58155). [CutyDina's 2D rigging tutorial](https://www.cutydina.com/2020/04/2dcharacters-blender2.8.html) dedicates a section to plane-specific weight paint workarounds.

**Distilled:** Blender's weight paint defaults assume 3D solid; for planar 2D the default "front faces only" silently makes half of every stroke disappear, and the fix requires two unrelated settings nobody finds without a tutorial.

**Implication for SPEC 013:** ship a 2D-aware weight paint mode preset that auto-disables Front Faces Only, enables 2D / projected falloff, locks symmetry to picker's mirror axis. Detect when active object is Proscenio-tagged 2D plane and force preset at mode-enter time. Surface preset state as header pill so user does not lose orientation when switching to non-Proscenio mesh.

### 2. Auto-Weights Failures ("Bone Heat Weighting: failed to find solution")

Single most-asked weight-related question on Blender Stack Exchange / BlenderArtists / GameDev.tv. Error opaque; causes many; fixes all empirical workarounds in sequence.

User signal: [BlenderNation aggregator](https://www.blendernation.com/2023/05/19/solutions-to-bone-heat-weighting-error/) lists top causes (densely packed vertices, non-manifold, overlapping verts, disconnected components, floating-point precision when small-and-far-from-origin). [GameDev.tv thread](https://community.gamedev.tv/t/bone-heat-weighting-failed-to-find-solution-for-one-or-more-bones/230350) - users iterating through scale-up tricks, normal recalcs, merge-by-distance. [T70834](https://developer.blender.org/T70834) confirms "Automatic Weights fail when object is small and far from world origin" is a real engine-level precision issue. [T37685](https://developer.blender.org/T37685) - "Automatic Weighting Fails Unless Normals Recalculated." [T45493](https://developer.blender.org/T45493) - failure caused by "none of the vertices in an island being visible to any bones." [Interference22 blog](https://interference22.wordpress.com/2023/08/09/blender-quick-tip-i-cant-get-automatic-weights-to-work-when-rigging/) is itself a top search result - the de facto remedy recipe (apply scale, recalc normals, merge by distance, scale up 10x, retry).

**Distilled:** Bone Heat Weighting fails opaquely from 5+ different root causes; user has to run a recipe of unrelated cleanups before retrying, and the error message says nothing actionable.

**Implication for SPEC 013:** Proscenio's auto-weights step must pre-flight: detect zero-area faces, overlapping verts, unapplied scale, far-from-origin position, flipped normals, isolated mesh islands before calling Blender's `parent_with_automatic_weights`. On failure, surface a structured diagnosis ("3 islands have no bone in line of sight - select bones B1, B2 to fix") not a stack trace. For 2D specifically, bone-heat's line-of-sight assumption is broken - SPEC 013 ships a custom planar-distance falloff weight algorithm instead of relying on Blender's heat solver.

### 3. Automesh / Mesh-From-Image Complaints

Across Spine, DragonBones, COA Tools, Blender - identical pattern: automesh produces a "starting point" that every serious rig requires manual rework on. Nobody ships density that adapts to where the user will actually deform.

User signal: [NightQuestGames DragonBones review](https://www.nightquestgames.com/dragonbones-animation-the-ultimate-animation-software-for-beginners/) - "AutoMesh allows you to automatically generate a mesh around an image, but unfortunately, the resulting meshes are not accurate enough. It can be a good tool for creating an initial mesh." [Spine forum Auto Mesh? thread](https://esotericsoftware.com/forum/d/5578-auto-mesh) is a long-running feature request showing the community keeps asking for better automesh year after year. Spine's own blog [mesh creation tips](https://esotericsoftware.com/blog/Mesh-creation-tips-vertex-placement) tells users to "start with the least number of vertices possible, only add vertices where required" - implicitly admitting the auto-mesh starting density is rarely right. [COA Tools issue #181](https://github.com/ndee85/coa_tools/issues/181) - users wanting variable density across one sprite; [COA tracker root](https://github.com/Aodaruma/coa_tools2) confirms "weight paint functionality doesn't work, which is only needed when you add more bones into one sprite" - the addon's automesh and weight system don't cooperate when the rig is non-trivial.

**Distilled:** Every shipping automesh is a uniform-density grid bounded by alpha; users want non-uniform density that thickens under joints and thins on flat fills, and they want it to update without losing weights when source PSD changes.

**Implication for SPEC 013:** Proscenio automesh should accept the picker's bone positions as input and locally subdivide under bone influence radii (more triangles where deformation happens). Expose two density knobs separately: silhouette resolution (alpha-driven hull) and interior resolution (bone-driven subdivision). Default to "auto under bones" when picker has an armature; uniform density when not. Treat automesh output as regenerable - record alpha threshold + bone-density params on the object so re-runs are deterministic and diffable.

### 4. Weight Paint Brush UX (General)

Brush itself accumulates 15+ years of papercuts: mirror unreliable, gradient ignores symmetry, tablet pressure breaks per-driver, mode crashes outright on undo for blur/smudge in current 4.5.

User signal: [#116115](https://projects.blender.org/blender/blender/issues/116115) - "Weight Paint Mode Mirror Vertex Groups not working." [T99668](https://developer.blender.org/T99668) - "Gradient Tool on Weight Paint Mode ignores X-Axis Symmetry Option." [T46254](https://developer.blender.org/T46254) - "X mirror weight paint doesn't work with some tools" (mirror is per-brush, not per-mode, invisible to users). [#149138](https://projects.blender.org/blender/blender/issues/149138) (4.5.3) - "Undoing while Using blur or Smudge in weight paint mode Crashes" (most basic recovery takes the program down in current LTS). [T75518](https://developer.blender.org/T75518) - "Weight paint brush: front faces only not working" (even the toggle 2D users depend on is buggy across versions). Tablet pressure graveyard: [T82432](https://developer.blender.org/T82432), [T73377](https://developer.blender.org/T73377), [#85844](https://projects.blender.org/blender/blender/issues/85844), [T93069](https://developer.blender.org/T93069). Performance: [T75452](https://developer.blender.org/T75452) - "RAM consumption spiking to more than 20GB, especially when increasing brush size."

**Distilled:** Brush is unreliable along three independent axes - mirror, tablet input, undo - and users learn to save before every stroke.

**Implication for SPEC 013:** Proscenio cannot fix Blender's tablet stack, but it can (a) auto-save a vertex-group snapshot before entering paint mode, (b) provide a one-click "restore last snapshot" not dependent on Blender's undo, (c) force-enable symmetry consistently across all paint tools when picker has a mirror axis configured. Surface mirror state in header (not buried in N-panel) so user can verify it's actually on. For 2D, lock brush size to ortho-pixel units rather than world units so brush size doesn't change meaning across zoom levels.

### 5. Iteration Loop Pain (Regen Mesh -> Lose Weights)

**The highest-leverage unsolved problem in the entire 2D rigging space.** Every major tool loses some or all weight data when geometry is regenerated, and the workaround (Data Transfer / weight projection) is fragile and confusingly configured.

User signal: [Blender bug #150016](https://projects.blender.org/blender/blender/issues/150016) - "Remesh converts vertex groups to regular attributes" (even the new remesh path silently mangles weight data into wrong storage class). [T87025](https://developer.blender.org/T87025) - "Remesh Wipes out Vertex Paint Data" (confirmed-and-tracked behaviour). Blender docs [explicitly state](https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/remesh.html) "The current voxel remesher only preserves face sets and mask data, any other geometry attribute is deleted." [DigitalProduction "Weight No More"](https://digitalproduction.com/2025/04/23/weight-no-more-streamlining-blenders-weight-painting-with-robust-weight-transfer/) headlines "an entire third-party addon ecosystem exists purely because the built-in Data Transfer is unreliable." [80.lv Robust Weight Transfer](https://80.lv/articles/grab-this-one-click-blender-tool-for-effortless-weight-transfers) - built on SIGGRAPH ASIA 2023 paper "Robust Skin Weights Transfer via Weight Inpainting" (academic field treats this as still-open research). Data Transfer's mapping options ("Nearest Face Vertex" vs "Nearest Face Interpolated" vs "Nearest Vertex" vs ...) confusingly configured - [BlenderArtists thread](https://blenderartists.org/t/transfer-weights-nearest-face-interpolated-doing-strange-things-in-2-76/655331).

**Distilled:** Regenerating the mesh destroys all weight-paint labor; official transfer tools require esoteric option choices and still produce wrong results on basic cases; entire third-party paid-addon market exists to paper over this.

**Implication for SPEC 013 (HIGHEST PRIORITY):**

- Proscenio must persist weights independently of the mesh - store them as a Proscenio sidecar (per-region weight stamps keyed by UV coordinates or alpha-landmark anchors, not vertex indices).
- On automesh regen, automatically reproject weights from the sidecar onto the new topology before the user notices.
- Provide a visible "weight provenance" indicator: each vertex's weight came from (a) user paint, (b) auto-projection from sidecar, or (c) fresh auto-weight default. Allow locking (a)-vertices against future automesh regens.
- **This is the single feature that, if shipped well, would differentiate Proscenio from every competitor including Spine.**

### 6. Community Wishlist - What Nobody Ships

User signal: [Spine forum "Some features Spine is actually missing"](https://en.esotericsoftware.com/forum/d/28041-some-features-spine-is-actually-missing) - vertex-level animation curves, dark-tint, runtime parity. [GameDev.net thread on 2D bone animation](https://www.gamedev.net/forums/topic/695897-is-it-possible-to-create-quality-animations-with-2d-bone-based-animation/) - "Spine turned out to be a very long and painful process for complex animations... a character needed to house all the bones and sprites for all their animations/poses." Same thread: "Vertices can't be animated in some tools, so you can't have ANY organic feel (like lungs breathing). Parent bone can't be animated without affecting the children" (Live2D/DragonBones constraint complaints). [arman-animation 2026 review](https://www.armanimation.com/post/best-2d-skeletal-animation-software-in-2026-free-paid-options-compared) - Spine's restrictive per-seat licensing as permanent pain. Same source on LoongBones/DragonBones rebrand backlash. [Axmol discussion #2528](https://github.com/axmolengine/axmol/discussions/2528) - users asking for a standalone skeleton animation editor because every existing one is locked to a vendor format.

**Recurring asks nobody ships:**

1. Mesh density that adapts to bone density / deformation hotspots.
2. Non-destructive iteration: change the source art, keep the weights and the rig.
3. Open file format that doesn't lock the project to one vendor.
4. Vertex-level animation that doesn't fight the bone hierarchy.
5. Per-seat licensing that doesn't tax every programmer on the team.
6. Integrated game-engine target without a separate runtime to maintain.
7. Symmetry that actually works across all paint tools without per-tool config.
8. Weight transfer that survives topology change without manual reprojection.

**Distilled:** Every existing tool optimizes for the first character rig and punishes iteration, team-scale, and engine integration.

**Implication for SPEC 013:** Proscenio's source-of-truth being plain .blend + sidecar JSON inside the user's repo already addresses (3), (5), (6). SPEC 013 should explicitly own (1), (2), (7), (8) - the mesh+weights deliverables. (4) vertex-level animation is out of SPEC 013 scope but is a strong candidate for SPEC 014.

### TL;DR for Proscenio - Top 5 Pain Points to NOT Replicate

1. **Silent default that breaks 2D paint** - never ship a "Front Faces Only" default on a 2D-tagged object. Proscenio plane preset must enable through-paint at mode-enter with a visible header pill.
2. **Opaque auto-weight failure with cryptic error** - never call `parent_with_automatic_weights` blind. Pre-flight scale, normals, overlapping verts, bone line-of-sight; on failure, surface the offending islands by name and offer the fix.
3. **Uniform-density automesh that forces manual rework** - never ship a single alpha-threshold knob as the only automesh control. Density must adapt under bone influence radii out of the box.
4. **Regen destroys weight labor** - never store weights only on current topology. Persist a weight sidecar keyed by alpha-stable anchors so automesh regen replays the user's paint automatically. **Single biggest differentiation opportunity.**
5. **Inconsistent symmetry across tools** - never let "mirror" be a per-brush setting hidden in submenus. Picker-defined mirror axis applies uniformly to brush, gradient, fill, blur, smooth; state visible from the header.

## Patterns observed across tools

Synthesis matrix. Pattern column = capability. Tool columns = ships it? (yes / no / partial / N/A for paradigm mismatch). Proscenio relevance column = first-cut, Wave 13.2, deferred / future.

| Pattern | Spine | DragonBones | Spriter 1.x | Live2D | Moho | Animate | Toon Boom | Blender native | COA2 | **Proscenio relevance** |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Alpha-trace automesh (one-shot from PNG) | yes (`Trace`) | no | no | yes (Auto Mesh Generation) | n/a (vector) | partial (auto-tri on joint placement) | n/a (deformer chains) | no | yes (cv2-dependent) | **first cut** (pure-Python alpha walker) |
| Iterative add-density automesh | yes (`Generate`) | no | no | yes (manual densify) | n/a | no | no | no | no | **Wave 13.2** |
| Density-under-bones (variable resolution) | partial (manual via tool) | no | no | partial (manual) | n/a | no | n/a | no | no | **first cut** (key differentiator) |
| Concave-hull silhouette boundary | yes | manual | n/a | yes | n/a | yes | yes | no | yes (cv2 contours) | **first cut** |
| Annulus topology (inner+outer contour + fill) | partial | no | no | partial | n/a | no | n/a | no | **yes** | **first cut** (lift from COA2) |
| Auto-bind from selected bones | yes (Auto) | yes (Bind+rightclick) | n/a | yes (Skinning op) | yes (region) | yes (joint placement implicit) | yes (chain) | yes (`Ctrl+P Auto`) | yes (uses Blender Auto) | **first cut** |
| Planar-safe auto-weights (no heat solver) | yes (proprietary) | yes (distance) | n/a | yes (deformer parent) | yes (region) | yes (proximity) | yes (chain bias) | **no** (heat fails on planes) | no (delegates to Blender) | **first cut** (custom planar falloff) |
| Per-vertex continuous weights | yes | yes | n/a | partial (Glue only) | partial (Bind Points) | no (binary) | no (region) | yes | yes (delegates) | **first cut** |
| Brush Add/Sub/Replace modes | yes | partial | n/a | n/a | n/a | no | n/a | yes | yes (Blender stack) | **first cut** (lift Blender presets) |
| 2D-aware brush radius (screen px, not world) | n/a (always 2D) | n/a | n/a | n/a | n/a | n/a | n/a | no | no | **first cut** (custom preset) |
| Symmetry mirror across user axis | no (community ask) | no | n/a | yes (PSD axis) | yes (X mirror) | yes (auto) | yes (group copy) | partial (X only, buggy) | no | **first cut** (mirror via picker axis) |
| Lock bones during paint (multi-bone exclude) | yes (Lock) | no | n/a | n/a | n/a | n/a | n/a | yes (vertex group lock) | no | **first cut** (lift Blender) |
| Smooth / blur brush | yes | yes (Smooth) | n/a | n/a | n/a | yes (Soft bone toggle) | yes (region blend) | yes (buggy on planes) | yes (delegates) | **Wave 13.2** (planar-safe blur) |
| Bone strength region as primary metaphor | no | no | n/a | partial (deformer reach) | **yes** (Strength tool) | partial (mesh density) | yes (Bias) | no | no | **Wave 13.2** (Moho lift) |
| Soft vs Hard bone toggle | no | no | n/a | n/a | n/a | yes | no | no | no | **Wave 13.2** (Animate lift) |
| Auto-patch joint cover at articulations | no | no | n/a | partial (Glue) | partial (Smart Bone) | no | **yes** (Auto-Patch node) | no | no | **Wave 13.3** (Harmony lift) |
| Snapshot mesh+weights on bind (rest-state) | partial | no | n/a | **yes** (Restore Deformer) | no | partial (keyframe undo) | yes (Deformation Group) | no | **yes** (`coa_base_sprite`) | **first cut** (THE differentiator) |
| Weight preservation on mesh regen | partial | no | n/a | yes (deformer-mesh independent) | yes (region-based) | partial (slider warning) | yes (chain independent) | **no** (remesh wipes) | partial (base sprite anchor only) | **first cut** (sidecar reproject) |
| Pre-flight diagnosis on auto-weight failure | n/a (no failure mode) | n/a | n/a | n/a | n/a | n/a | n/a | **no** (cryptic error) | no | **first cut** (structured guidance) |
| GPU overlay weight viz (custom, not native heatmap) | yes (Direct mode) | yes (pie chart per vert) | n/a | n/a | n/a | n/a | n/a | partial (vertex display) | **yes** (6-stop colorband discs) | **first cut** (lift COA2) |
| One-button modal wrapper for paint mode | n/a | n/a | n/a | n/a | n/a | n/a | n/a | no | **yes** (Edit Weights) | **first cut** (lift COA2) |
| ESC always exits modal | yes | yes | n/a | yes | yes | yes | yes | yes | **no** (deselect only) | **first cut** (hard contract) |
| Tablet pressure handled in draw modal | unclear | n/a | n/a | yes | yes | yes (draw tools) | yes | yes (when drivers cooperate) | **no** (zero hits in code) | **first cut** (event.pressure + release detection) |
| Weight transfer between sprites (rig clone) | n/a (single mesh) | n/a | n/a | yes (Glue across ArtMeshes) | yes (Copy/Paste Bone Actions) | n/a | yes (Weighted Deform sources) | yes (Data Transfer modifier) | no (issue #18 #73 open) | **Wave 13.2** |
| Live pose-mode preview in weight paint | n/a (modes share) | n/a | n/a | n/a | yes | yes (timeline scrub) | yes | partial (with workarounds) | partial (POSE+WEIGHT_PAINT split via modal) | **first cut** (lift COA2 pattern) |

**First-cut column = SPEC 013 Wave 13.1 minimum viable shape.** Wave 13.2 = follow-up productivity wave. Wave 13.3+ = aspirational (Auto-Patch, Smart Bones). Future / deferred = successor SPECs.

## Position of Proscenio today

Mapping current state to first-cut patterns above:

| Area | Status today | File / handle |
| --- | --- | --- |
| Skinning emit (writer -> `weights` array) | **shipped** (SPEC 003) | [`exporters/godot/writer/sprites.py`](../../apps/blender/exporters/godot/writer/sprites.py) `_build_sprite_weights` |
| Skinning import (`Polygon2D.skeleton` + `add_bone`) | **shipped** (SPEC 003) | [`apps/godot/addons/proscenio/builders/polygon_builder.gd`](../../apps/godot/addons/proscenio/builders/polygon_builder.gd) |
| Quick Armature (bone authoring) | **shipped** (SPEC 012) | [`operators/quick_armature.py`](../../apps/blender/operators/quick_armature.py) |
| Active armature picker (source of truth) | **shipped** (SPEC 012 D16) | [`properties/scene_props.py`](../../apps/blender/properties/scene_props.py) `active_armature` |
| Modal overlay scaffold (GPU draw + status / header hints) | **shipped** (SPEC 012) | [`core/bpy_helpers/modal_overlay.py`](../../apps/blender/core/bpy_helpers/modal_overlay.py) |
| Photoshop `[mesh]`-tagged layer ingest | **shipped** (SPEC 011) | [`importers/photoshop/planes.py`](../../apps/blender/importers/photoshop/planes.py) |
| Alpha-trace automesh from sprite | **no** | gap (this SPEC) |
| Annulus topology (outer+inner contour + fill) | **no** | gap (this SPEC) |
| Planar-safe auto-weights (no heat solver) | **no** | gap (this SPEC) |
| Auto-vertex-group from bone chain | **no** | gap (this SPEC) |
| 2D-aware weight paint preset (Front Faces off, 2D Falloff, mirror via picker) | **no** | gap (this SPEC) |
| GPU overlay weight viz (per-vertex colorband) | **no** | gap (this SPEC) |
| One-button modal wrapper for paint mode | **no** | gap (this SPEC) |
| Weight sidecar (preserve through regen) | **no** | gap (this SPEC, **key differentiator**) |
| Pre-flight diagnosis on auto-weight failure | **no** | gap (this SPEC) |
| Mesh-data preservation anchor (base sprite verts survive regen) | **no** | gap (this SPEC) |
| Tablet release detection in draw modal | **no** | gap (this SPEC, lifecycle hygiene) |
| Soft vs Hard bone toggle | **no** | Wave 13.2 |
| Bone strength region painting | **no** | Wave 13.2 |
| Auto-patch joint cover | **no** | Wave 13.3 |
| Weight transfer between sprites | **no** | Wave 13.2 |

11 first-cut gaps in this SPEC. Wave 13.1 ships them; Waves 13.2 / 13.3 ship the productivity + aspirational layers.

## Design surface

The SPEC splits into five concerns:

1. **Mesh generation (automesh).** Pure-Python alpha-contour walker (Moore neighbour or marching squares on `bpy.types.Image.pixels` buffer - no OpenCV) builds outer + inner contour + annulus triangulation. Configurable resolution, alpha threshold, margin. Re-runnable with `coa_base_sprite`-style preservation anchor.
2. **Bone binding + initial weights.** Custom planar-distance falloff algorithm (NOT bone heat). Takes the active mesh + the active armature picker's target, walks the bone chain, creates one vertex group per bone, seeds with planar proximity weights. Fallback to "empty groups" and "1.0 to single nearest" modes. Pre-flight checks before any call to vanilla `parent_with_automatic_weights` (kept as fallback only on explicit user request).
3. **Weight paint modal wrapper.** One-button enter / exit. On invoke: snapshot vertex groups, force 2D-safe brush preset (Front Faces Only off, 2D Falloff on, brush radius in screen pixels), enable Auto Normalize, switch armature to POSE + mesh to WEIGHT_PAINT, auto-select vertex group matching first selected bone. Custom GPU overlay (colorband discs per vertex, lifted from COA2). On exit: restore everything. ESC = hard exit. Tablet RELEASE detection via `event.pressure==0` + `WINDOW_DEACTIVATE` + timer fallback.
4. **Iteration loop (weight preservation).** Sidecar JSON stored on the mesh object as `obj["proscenio_weight_sidecar"]` (raw Custom Property, durable through addon disable). Captures (a) vertex group names, (b) per-vertex weights keyed by alpha-stable UV anchors (not vertex indices), (c) mesh-data-hash baseline. On automesh regen: detect topology change, reproject sidecar onto new vertices via nearest-UV-neighbour interpolation, emit "weight provenance" report (X paint vertices restored, Y new vertices seeded from proximity falloff). Vertex provenance overlay distinguishes the three sources visually.
5. **Subpanel + operator surface.** New `Skinning` subpanel parallel to `Skeleton` in the Proscenio sidebar. Buttons: `Automesh from Sprite`, `Bind to Picker Armature`, `Edit Weights` (modal wrapper), `Mirror Weights`, `Restore Snapshot`. Header pill shows picker armature + current bind mode + 2D paint preset status.

### Layout and integration points

- **Operators**: `proscenio.automesh_from_sprite`, `proscenio.bind_mesh_to_armature`, `proscenio.edit_weights_modal`, `proscenio.mirror_weights`, `proscenio.restore_weight_snapshot`, `proscenio.diagnose_weight_failure`. Invocable from the Skinning subpanel and from F3 search.
- **Panel**: `Skinning` subpanel inside the Proscenio sidebar, alongside `Skeleton`. Shows the active mesh's vertex groups, binding status (bound to picker armature? which bones have non-empty weights? which are orphan?), preset state, the operator buttons.
- **Active armature picker** (`scene.proscenio.active_armature`) - canonical source of truth (SPEC 012 D16 contract).
- **Active sprite** (`scene.proscenio.active_sprite`) tells which mesh receives operations.
- **Modal overlay scaffold** (`core/bpy_helpers/modal_overlay.py`) - lift for the GPU weight overlay + the edit-weights status hints.

### Property model

```python
class ProscenioSkinningProps(bpy.types.PropertyGroup):
    automesh_resolution: FloatProperty(
        name="Mesh resolution",
        description="Lower values produce more vertices (image downscale factor)",
        default=0.25,
        min=0.01,
        max=1.0,
    )
    automesh_alpha_threshold: IntProperty(
        name="Alpha threshold",
        description="Pixels above this alpha value contribute to the mesh boundary",
        default=127,
        min=0,
        max=255,
    )
    automesh_margin: FloatProperty(
        name="Boundary margin",
        description="Dilate (outer) / erode (inner) the contour by this many pixels - controls annulus thickness",
        default=5.0,
        min=0.0,
        max=100.0,
    )
    automesh_density_under_bones: BoolProperty(
        name="Density follows bones",
        description="Subdivide more under the picker armature's bones (more triangles where deformation happens)",
        default=True,
    )
    bind_init_mode: EnumProperty(
        name="Initial weights",
        items=[
            ("PROXIMITY", "Proximity (planar)", "Seed weights from planar distance-to-bone (default - safest for 2D)"),
            ("ENVELOPE", "Envelope", "Seed weights from bone envelope radius"),
            ("SINGLE_NEAREST", "Single nearest", "1.0 weight to the closest bone per vertex (hard binding)"),
            ("EMPTY", "Empty groups", "Create vertex groups but leave weights at zero (paint everything manually)"),
        ],
        default="PROXIMITY",
    )
    preserve_on_regen: BoolProperty(
        name="Preserve weights on regen",
        description="Snapshot weights before automesh regen + reproject after",
        default=True,
    )
    paint_preset_2d: BoolProperty(
        name="2D paint preset",
        description="Auto-apply 2D-safe brush settings (Front Faces Only off, 2D Falloff on, brush radius in screen px) on Edit Weights",
        default=True,
    )
```

Lives at `scene.proscenio.skinning`. Naming pattern parallel to `scene.proscenio.quick_armature` (SPEC 012 D15).

### Out of scope (deferred to successor SPECs or backlog)

- **Auto-attach mesh to slot.** Coupling between vertex groups and SPEC 004 slot system; deferred until SPEC 004 maturity.
- **Bezier brush stroke for the alpha-boundary trace.** COA Tools 2 uses straight-segment strokes; SPEC 013 follows the same minimal model.
- **GPU-accelerated weight sampling.** All weight math is bmesh + Python loops. If performance becomes a complaint on >5000-vertex meshes, escalate to backlog.
- **Multi-mesh batch bind.** Operator targets a single active mesh. Batch bind = Wave 13.2 candidate.
- **Live2D-style deformer paradigm.** Proscenio is bone-based; deformers are a different SPEC entirely if ever pursued.
- **Soft vs Hard bone toggle (Adobe Animate lift)** - Wave 13.2 candidate; first-cut delivers proximity falloff which behaves like "soft" by default.
- **Bone strength region painting (Moho lift)** - Wave 13.2 candidate; foundational and high-value but requires a custom widget + viewport draw that doubles SPEC scope if first-cut.
- **Auto-patch joint cover at articulations (Toon Boom Harmony lift)** - Wave 13.3 candidate; requires both child-mesh detection and a custom seam generator.
- **Smart-Bone-style corrective drivers** - SPEC 014+ material; couples to animation system not authoring.
- **Cubism Glue equivalent** (seam binding between two ArtMeshes) - Wave 13.3.
- **Mirror humanoid binding** (one mesh on one side, click to mirror to the other) - couples to symmetric rigs. Currently no Proscenio fixture exercises symmetric humanoids end-to-end. Trigger: first humanoid fixture lands.

## Design decisions (locked)

| ID | Question | Locked answer | Wave |
| --- | --- | --- | --- |
| D1 | Automesh paradigm | **A** alpha-trace one-shot (pure-Python, no OpenCV) | 1 |
| D2 | Mesh topology shape | **B** annulus (outer + inner contour + triangle_fill) | 1 |
| D3 | Mesh data preservation anchor | **A** `proscenio_base_sprite` vertex group | 1 |
| D4 | Bone heat solver usage | **C** explicit user opt-in only, NEVER default | 1 |
| D5 | Initial bind algorithm default | **C** planar proximity falloff (custom, NOT bone heat) | 1 |
| D6 | Weight preservation through mesh regen | **A** sidecar JSON keyed by UV anchors + auto-reproject | 1 |
| D7 | Weight paint modal wrapper | **A** one-button enter / exit, auto-restore on exit + crash | 1 |
| D8 | 2D paint preset application | **A** auto-apply on Edit Weights modal enter, header pill visible | 1 |
| D9 | GPU weight overlay viz | **A** colorband discs per vertex (lift from COA2) | 1 |
| D10 | ESC handling in draw modal | **A** hard exit + release pending stroke | 1 |
| D11 | Pre-flight diagnosis on auto-weight failure | **A** structured guidance per failure cause, never raw stack trace | 1 |
| D12 | Tablet RELEASE detection | **C** `event.pressure==0` + `WINDOW_DEACTIVATE` + timer fallback | 1 |
| D13 | Subpanel placement | **A** new `Skinning` subpanel parallel to `Skeleton` | 1 |
| D14 | Symmetry mirror axis source | **A** picker armature mirror flag (single source of truth) | 1 |
| D15 | Density-under-bones automesh | **A** ON by default when picker has armature, OFF otherwise | 1 |
| D16 | Soft vs Hard bone toggle | **B** defer to Wave 13.2 | 13.2 |

Each section below preserves the option set + rationale for posterity.

### D1 - Automesh paradigm: alpha-trace, free-draw stroke, or hybrid?

- D1.A - **Alpha-trace one-shot from PNG.** Detect contour from image alpha + threshold, triangulate inside with target vertex count. One operator, one click, zero strokes. Spine `Trace` / Cubism AutoMesh / Animate Asset Warp ship this.
- D1.B - Free-draw stroke (a la COA Tools 2 "Draw 2D Polygon"). User clicks vertices around the silhouette; modal closes when stroke closes; tessellate inside. Higher control, requires modal scaffold + tablet handling.
- D1.C - Hybrid - auto-trace boundary, user can refine in edit modal before tessellation.

**Locked: D1.A.** Most user flows in the survey want "one click, sane default" before reaching for manual refinement. Free-draw (D1.B) is COA2's primary surface and is bug-prone exactly because it requires perfect modal lifecycle hygiene (the very bug in the user-supplied screenshot). Hybrid (D1.C) doubles the operator surface for marginal benefit on the first cut. SPEC 013 ships D1.A; D1.B + D1.C become Wave 13.2 additions if real workflows demand them. Pure-Python alpha walker (no OpenCV) is non-negotiable per Constraints.

### D2 - Mesh topology shape: flat triangulation or annulus?

- D2.A - Flat triangulation. Single contour from alpha, fill interior. Spine `Trace` default.
- D2.B - **Annulus (outer dilate + inner erode + triangle_fill).** COA Tools 2's pattern. Produces a ring of dense edge loops near silhouette + interior coverage. Deforms predictably under bones.
- D2.C - Variable density flat triangulation (density spike near bones).

**Locked: D2.B.** COA2 has the right answer here; flat triangulation produces ugly silhouette triangles that bend awkwardly. Annulus is also more amenable to D15's density-under-bones because the bone-density layer can subdivide only the interior fill without touching the silhouette ring. D2.C is captured separately by D15 - this decision is about the topology shape, not the density distribution.

### D3 - Mesh data preservation anchor

- D3.A - **`proscenio_base_sprite` vertex group.** Tag the original 4 corner verts in a named vertex group at automesh time. Re-runs of automesh remove only verts NOT in this group, so the UV-pinned base survives forever. Lift directly from COA2's `coa_base_sprite` pattern.
- D3.B - Mesh-data hash + diff. Track which verts the user touched manually; preserve only those.
- D3.C - No preservation - regen always rebuilds from scratch.

**Locked: D3.A.** COA2's pattern is proven and trivial to implement. Hash-and-diff (D3.B) is sophisticated but harder to make legible to the user. D3.C is the COA pre-PR-#113 behaviour and is the reason the screenshot-bug-A "sprite vanishes on resolution change" happens. The preservation anchor is also what makes D6 (weight sidecar reproject) tractable - we always know which verts are "original base" vs "automesh-generated" vs "user-added."

### D4 - Bone heat solver usage

- D4.A - Default to bone heat (Blender vanilla behaviour).
- D4.B - Wrap bone heat with pre-flight; default to it if pre-flight passes.
- D4.C - **Explicit user opt-in only, NEVER default.** Bone heat is offered behind a checkbox in F3 redo or operator option; default bind never calls it.

**Locked: D4.C.** Bone heat fails on the exact topology Proscenio targets (planar 2D meshes). Every survey signal (Stack Exchange #1 question, T45493, T70834, T37685) confirms this. Defaulting to it would replicate the worst pain in vanilla Blender 2D rigging. Power users who *want* bone heat for specific topology can opt in via the F3 redo or by switching `bind_init_mode` to a future "BONE_HEAT" enum value (currently not even an option in D5). The right default is planar proximity (D5.C).

### D5 - Initial bind algorithm default

- D5.A - Empty vertex groups only. User paints from zero.
- D5.B - Envelope from bone capsule. Each bone's envelope radius drives initial influence.
- D5.C - **Planar proximity falloff (custom, NOT bone heat).** Per-vertex weight = 1 / planar-distance-to-bone-segment, normalized across bones, with a configurable falloff curve. Bone heat surface-diffusion assumptions removed entirely.
- D5.D - Bone heat (vanilla Blender). Known to fail on planar meshes.
- D5.E - Single nearest. 1.0 weight to the closest bone per vertex (hard binding).

**Locked: D5.C as default, D5.A / D5.B / D5.E offered via `bind_init_mode` enum, D5.D dropped from defaults per D4.** Planar proximity is the algorithm Animate uses (proximity-based) and DragonBones uses ("relative position"); it is robust on planar meshes by construction, gives sane initial weights for most rigs, and degrades gracefully (worst case: bones far from mesh get 0 weight, which is correct). Envelope (D5.B) is reasonable as a "more rigid" alternative for cutout-style rigs where bleed between body parts is undesired. Empty (D5.A) and Single Nearest (D5.E) cover the manual-paint and hard-binding cases respectively. Bone heat dropped from defaults per D4.

### D6 - Weight preservation through mesh regen

- D6.A - **Sidecar JSON keyed by UV anchors + auto-reproject.** Snapshot vertex weights before regen; on regen, reproject by nearest-UV-neighbour interpolation; surface weight-provenance overlay distinguishing user-paint / auto-projection / fresh-seed.
- D6.B - Snapshot vertex weights by vertex index; on regen warn that indices changed and ask the user to manually transfer.
- D6.C - No preservation. Document workflow as "regen first, paint after."
- D6.D - Defer entirely - rely on Blender's Data Transfer modifier.

**Locked: D6.A.** This is the single biggest differentiation opportunity vs every surveyed tool. Every competitor (Spine, COA2, Blender native, even Cubism) loses some weight data on topology change. Storing the sidecar keyed by UV (which is alpha-stable for cutout sprites with locked-base-sprite UVs per D3) means the reproject is deterministic and replayable. Provenance overlay (built on D9's GPU overlay scaffold) tells the user exactly which weights survived and which are fresh seeds, so they can verify and re-touch without surprise. D6.B is half-measure: the warning is correct but the manual transfer is the actual pain we are trying to avoid. D6.D punts the differentiation.

### D7 - Weight paint modal wrapper

- D7.A - **One-button enter / exit, auto-restore on exit + crash.** Lift COA2's `COATOOLS2_OT_EditWeights` pattern - on invoke snapshot all the brush + viewport + bone-collection state, switch to WEIGHT_PAINT + POSE, force 2D preset, auto-select first vertex group matching active bone. On exit (or crash via try/finally) restore everything.
- D7.B - No wrapper. User uses native Blender Weight Paint mode.
- D7.C - Wrapper only for state snapshot; do not touch brush or preset settings.

**Locked: D7.A.** The modal wrapper is the COA2 ergonomic win that users will notice immediately. Native Blender Weight Paint mode requires manually toggling 6+ settings every session; the wrapper collapses that into one button. Critical fixes vs COA2: (a) use Blender 4.0+ Bone Collections for visibility (undo-stack-aware) instead of `bone.hide` global flag, (b) wrap the modal body in a `try/finally` that calls the restore path on any exception (issue #109 traceback shows COA2's modal can leave the user with a half-broken viewport), (c) ESC always exits.

### D8 - 2D paint preset application

- D8.A - **Auto-apply on Edit Weights modal enter, header pill visible.** Force `Front Faces Only = False`, `Falloff Shape = Projected` (a.k.a. 2D Falloff), brush radius in screen pixels (custom unit conversion), `Auto Normalize = True`. Display "2D paint preset: ON" header pill. Restore prior brush state on exit.
- D8.B - Add operator buttons to toggle each setting individually; user opts in.
- D8.C - Don't ship - document the manual setup.

**Locked: D8.A.** Theme 1 from community pain is unambiguous: every 2D Blender user discovers Front Faces Only the hard way, often by giving up entirely. Forcing the preset at modal-enter time is the single most impactful UX win. Header pill makes the state legible so the user does not get confused when switching to non-Proscenio meshes. Per-setting opt-in (D8.B) defeats the purpose - users would not know which settings to toggle.

### D9 - GPU weight overlay viz

- D9.A - **Colorband discs per vertex (lift from COA2).** 6-stop colorband (red->orange->yellow-green->green->cyan->blue), filled disc per vertex sized to viewport scale, alpha 0 for zero-weight verts.
- D9.B - Use Blender's native weight heatmap only.
- D9.C - Custom overlay only for weight-provenance (D6), use native for value viz.

**Locked: D9.A.** Theme 4 from community pain notes Blender's native heatmap washes out under 0.15 weight; on low-poly meshes (which Proscenio's automesh deliberately produces) there is no gradient to read. COA2's per-vertex disc with explicit colorband is the right viz. Overlay also serves D6's provenance display - per-vertex color can encode either weight value OR provenance source via a toggle in the panel.

### D10 - ESC handling in draw modal

- D10.A - **ESC = hard exit + release pending stroke.** No conditions. The single contract.
- D10.B - ESC = deselect verts only (current COA2 behaviour, root cause of screenshot bug B).
- D10.C - ESC = exit if no active stroke, deselect otherwise.

**Locked: D10.A.** Universal contract across every other surveyed tool. COA2 is the lone outlier and the bug is documented in the user-supplied screenshot. Conditional ESC (D10.C) introduces ambiguity exactly when the user is panicking; hard exit is safer.

### D11 - Pre-flight diagnosis on auto-weight failure

- D11.A - **Structured guidance per failure cause, never raw stack trace.** Pre-flight detects unapplied scale, flipped normals, overlapping verts, isolated islands, bones outside mesh bbox; emits actionable message ("3 islands have no bone in line of sight - select bones B1, B2 to fix" or "Mesh has unapplied scale - press `Ctrl+A` -> Scale before binding").
- D11.B - Pass through Blender's raw error.
- D11.C - Pre-flight only, no diagnosis (silent fail-safe).

**Locked: D11.A.** Theme 2 from community pain is the #1 unsolved-by-default-Blender pain. Even with planar proximity as default (D5.C) - which sidesteps bone-heat-specific failures - we still want pre-flight against scale / normals / orphan islands because all four root causes apply to ANY bind algorithm. Structured guidance also serves as documentation surface: each diagnosis links to the relevant remedy.

### D12 - Tablet RELEASE detection

- D12.A - Listen for `LEFTMOUSE` RELEASE only (Blender default - root cause of screenshot bug B on Windows Ink tablets).
- D12.B - Listen for `LEFTMOUSE` RELEASE + `WINDOW_DEACTIVATE`.
- D12.C - **`event.pressure==0` + `WINDOW_DEACTIVATE` + timer-based fallback (synthesize RELEASE if no movement for N ms).**

**Locked: D12.C.** Tablet pressure dropping to 0 is the most reliable pen-lift signal across drivers (more reliable than RELEASE which Windows Ink sometimes drops); `WINDOW_DEACTIVATE` catches alt-tab + focus-loss; the timer fallback catches the worst-case driver glitch. Bug graveyard ([T82432](https://developer.blender.org/T82432), [T73377](https://developer.blender.org/T73377), [T93069](https://developer.blender.org/T93069)) shows Blender itself cannot make these guarantees; Proscenio's draw modal must be defensive.

### D13 - Subpanel placement

- D13.A - **New `Skinning` subpanel parallel to `Skeleton`.**
- D13.B - Extend `Skeleton` subpanel with a Skinning section.
- D13.C - Inline on active sprite panel.

**Locked: D13.A.** Parallel structure to SPEC 012's Skeleton panel; clear semantic separation (Skeleton = bones, Skinning = mesh+weights). Extending Skeleton (D13.B) would crowd the existing Quick Armature surface. Inline (D13.C) splits the operator surface across multiple panels and hurts discoverability.

### D14 - Symmetry mirror axis source

- D14.A - **Picker armature mirror flag (single source of truth).** When the active armature (`scene.proscenio.active_armature`) has a mirror axis configured, the mirror axis applies uniformly to brush, gradient, fill, blur, smooth for Proscenio's paint preset.
- D14.B - Per-operator axis option.
- D14.C - Use Blender's per-brush mirror.

**Locked: D14.A.** Single source of truth principle, parallel to SPEC 012 D16 "picker is the contract." Theme 4 from community pain is unambiguous: per-brush mirror is the wrong default and users cannot find it. Mirror state is also rendered in the header pill alongside the 2D paint preset state per D8.

### D15 - Density-under-bones automesh

- D15.A - **ON by default when picker has armature, OFF otherwise.** Automesh detects bone positions from the picker armature and locally subdivides the annulus interior fill under each bone influence radius. When no armature is set, falls back to uniform interior density.
- D15.B - Always uniform density.
- D15.C - User toggle, default OFF.

**Locked: D15.A.** Theme 3 from community pain identifies this as the key unshipped feature across all surveyed tools (Spine forum has multi-year request thread). Doing the bone-aware densification by default when an armature is present means new users get the better result without needing to know the feature exists; users without an armature get the safe uniform default. The implementation reuses bone positions already exposed via the picker contract (SPEC 012 D16) so no new picker / state is needed.

### D16 - Soft vs Hard bone toggle (Animate lift)

- D16.A - First cut.
- D16.B - **Defer to Wave 13.2.**
- D16.C - Don't ship.

**Locked: D16.B.** First cut already ships `bind_init_mode` with four options (PROXIMITY, ENVELOPE, SINGLE_NEAREST, EMPTY) per D5 - this covers the "soft" (PROXIMITY) and "hard" (SINGLE_NEAREST) cases at bind time. The Animate-style runtime toggle (where soft / hard can be flipped per-bone after bind and weights re-derive) is a productivity polish, not a first-cut blocker. Wave 13.2.

## Successor considerations

- **SPEC 004 (slots)** interacts with skinned meshes when a slot swap changes the attachment mesh. Each attachment already carries its own `weights` (SPEC 003 D7 model). SPEC 013 outputs feed this without further changes. Auto-copy weights across slot attachments is a Wave 13.2 candidate (parallels COA2 issue [#73](https://github.com/Aodaruma/coa_tools2/issues/73)).
- **Photoshop importer (SPEC 011)** evolution: a `[mesh:HIGH]` tag could let the artist hint at desired automesh resolution per layer at PSD authoring time. Out of scope here; backlog-worthy follow-up if real workflows surface it.
- **Live weight-paint preview in Pose mode** ("pose the bone, see how the mesh deforms in real time without leaving Weight Paint") is a Blender native feature with known papercuts (mode toggle latency, no painting from rest pose). Edit Weights wrapper (D7) already touches both POSE + WEIGHT_PAINT modes; a Wave 13.2 follow-up could add a "scrub to pose, return to rest" affordance without leaving the modal.
- **Soft vs Hard bone toggle (D16)** - Wave 13.2 per locked decision.
- **Bone strength region painting (Moho lift)** - Wave 13.2. Region widget + viewport draw doubles SPEC scope if first-cut.
- **Auto-patch joint cover at articulations (Toon Boom Harmony lift)** - Wave 13.3. Requires child-mesh detection + custom seam generator + integration with slot system.
- **Cubism Glue equivalent** (seam binding between two ArtMeshes) - Wave 13.3. Different operator surface than Auto-Patch (covers any seam, not just articulations).
- **Smart-Bone-style corrective drivers** - SPEC 014+. Couples to animation system not authoring.
- **Quick Mesh operator** (mentioned in SPEC 012 successor list) is the direct sibling to automesh; lift the modal scaffold from this SPEC if pursued.
- **Mirror humanoid binding** (one mesh on one side, click to mirror to the other) - couples to symmetric rigs. No Proscenio fixture exercises symmetric humanoids end-to-end today.
- **Multi-mesh batch bind** - apply auto-weights to N selected meshes in one operation. Wave 13.2.
- **Weight transfer between sprites** (rig clone across near-duplicate sprites - line / colour / shadow layered Live2D-style) - Wave 13.2. Foundational request open since COA2 inception ([#18](https://github.com/Aodaruma/coa_tools2/issues/18), [#73](https://github.com/Aodaruma/coa_tools2/issues/73)).
