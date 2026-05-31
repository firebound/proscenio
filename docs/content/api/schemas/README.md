# README

## Top-level Schemas

* [Proscenio PSD manifest](./psd_manifest.md "Root of a PSD manifest v2 document") – `https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json`

* [Proscenio character](./proscenio.md "Root of a ") – `https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json`

## Other Schemas

### Objects

* [Animation](./proscenio-defs-animation.md) – `https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Animation`

* [Bone](./proscenio-defs-bone.md) – `https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Bone`

* [FrameEntry](./psd_manifest-defs-frameentry.md) – `https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/FrameEntry`

* [Key](./proscenio-defs-key.md) – `https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Key`

* [PolygonLayer](./psd_manifest-defs-polygonlayer.md "Single PNG, single quad mesh") – `https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer`

* [PolygonSprite](./proscenio-defs-polygonsprite.md "Cutout-style sprite rendered as a Godot Polygon2D - vertices + UV") – `https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite`

* [Skeleton](./proscenio-defs-skeleton.md) – `https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Skeleton`

* [Slot](./proscenio-defs-slot.md) – `https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Slot`

* [SpriteFrameLayer](./psd_manifest-defs-spriteframelayer.md "N frames, single quad mesh, animated via proscenio") – `https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer`

* [SpriteFrameSprite](./proscenio-defs-spriteframesprite.md "Spritesheet sprite rendered as a Godot Sprite2D") – `https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite`

* [Track](./proscenio-defs-track.md) – `https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Track`

* [Weight](./proscenio-defs-weight.md) – `https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Weight`

### Arrays

* [Attachments](./proscenio-defs-slot-properties-attachments.md) – `https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Slot/properties/attachments`

* [Bones](./proscenio-defs-skeleton-properties-bones.md) – `https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Skeleton/properties/bones`

* [Frames](./psd_manifest-defs-spriteframelayer-properties-frames.md) – `https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/frames`

* [Keys](./proscenio-defs-track-properties-keys.md) – `https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Track/properties/keys`

* [Layers](./psd_manifest-properties-layers.md "Z-ordered top-to-bottom") – `https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/properties/layers`

* [Offset](./proscenio-defs-spriteframesprite-properties-offset.md) – `https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/offset`

* [Polygon](./proscenio-defs-polygonsprite-properties-polygon.md) – `https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/polygon`

* [Position](./psd_manifest-defs-polygonlayer-properties-position.md "PSD top-left bbox of the layer in pixels") – `https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/position`

* [Position](./psd_manifest-defs-spriteframelayer-properties-position.md "PSD top-left bbox of the largest frame") – `https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/position`

* [Size](./psd_manifest-defs-polygonlayer-properties-size.md "Layer bbox size in pixels") – `https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/size`

* [Size](./psd_manifest-defs-spriteframelayer-properties-size.md "Largest frame bbox size in pixels (importer pads smaller frames to match)") – `https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/size`

* [Size](./psd_manifest-properties-size.md "\[doc_width_px, doc_height_px]") – `https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/properties/size`

* [Sprites](./proscenio-properties-sprites.md) – `https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/properties/sprites`

* [Texture Region](./proscenio-defs-polygonsprite-properties-texture-region.md "\[x, y, width, height] in atlas pixels") – `https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/texture_region`

* [Tracks](./proscenio-defs-animation-properties-tracks.md) – `https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Animation/properties/tracks`

* [Untitled array in Proscenio PSD manifest](./psd_manifest-defs-polygonlayer-properties-origin-anyof-0.md) – `https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/origin/anyOf/0`

* [Untitled array in Proscenio PSD manifest](./psd_manifest-defs-spriteframelayer-properties-origin-anyof-0.md) – `https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/origin/anyOf/0`

* [Untitled array in Proscenio PSD manifest](./psd_manifest-properties-anchor-anyof-0.md) – `https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/properties/anchor/anyOf/0`

* [Untitled array in Proscenio character](./proscenio-defs-key-properties-position-anyof-0.md) – `https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Key/properties/position/anyOf/0`

* [Untitled array in Proscenio character](./proscenio-defs-key-properties-scale-anyof-0.md) – `https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Key/properties/scale/anyOf/0`

* [Untitled array in Proscenio character](./proscenio-defs-bone-properties-position-anyof-0.md) – `https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Bone/properties/position/anyOf/0`

* [Untitled array in Proscenio character](./proscenio-defs-bone-properties-scale-anyof-0.md) – `https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Bone/properties/scale/anyOf/0`

* [Untitled array in Proscenio character](./proscenio-defs-polygonsprite-properties-polygon-items.md) – `https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/polygon/items`

* [Untitled array in Proscenio character](./proscenio-defs-polygonsprite-properties-uv-items.md) – `https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/uv/items`

* [Untitled array in Proscenio character](./proscenio-defs-polygonsprite-properties-weights-anyof-0.md) – `https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/weights/anyOf/0`

* [Untitled array in Proscenio character](./proscenio-defs-spriteframesprite-properties-texture-region-anyof-0.md "\[x, y, width, height] in atlas pixels") – `https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/texture_region/anyOf/0`

* [Untitled array in Proscenio character](./proscenio-properties-animations-anyof-0.md) – `https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/properties/animations/anyOf/0`

* [Untitled array in Proscenio character](./proscenio-properties-slots-anyof-0.md) – `https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/properties/slots/anyOf/0`

* [Uv](./proscenio-defs-polygonsprite-properties-uv.md) – `https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/uv`

* [Values](./proscenio-defs-weight-properties-values.md) – `https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Weight/properties/values`
