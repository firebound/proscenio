# SpriteFrameSprite Schema

```txt
https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/properties/sprites/items/oneOf/1
```

Spritesheet sprite rendered as a Godot Sprite2D.

`frame` indexes into an `hframes` x `vframes` grid carved
out of the atlas (or out of `texture_region` when present).

Field declaration order mirrors the writer's dict insertion order
so `model_dump_json(exclude_unset=True)` reproduces the golden
fixtures byte-for-byte once the writer migrates.

| Abstract            | Extensible | Status         | Identifiable | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                              |
| :------------------ | :--------- | :------------- | :----------- | :---------------- | :-------------------- | :------------------ | :-------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | No           | Forbidden         | Forbidden             | none                | [proscenio.schema.json\*](../../../../out/proscenio.schema.json "open original schema") |

## 1 Type

`object` ([SpriteFrameSprite](proscenio-defs-spriteframesprite.md))

## 1 Properties

| Property                           | Type      | Required | Nullable       | Defined by                                                                                                                                                                                                               |
| :--------------------------------- | :-------- | :------- | :------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [bone](#bone)                      | `string`  | Required | cannot be null | [Proscenio character](proscenio-defs-spriteframesprite-properties-bone.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/bone")                     |
| [centered](#centered)              | `boolean` | Optional | cannot be null | [Proscenio character](proscenio-defs-spriteframesprite-properties-centered.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/centered")             |
| [frame](#frame)                    | `integer` | Optional | cannot be null | [Proscenio character](proscenio-defs-spriteframesprite-properties-frame.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/frame")                   |
| [hframes](#hframes)                | `integer` | Required | cannot be null | [Proscenio character](proscenio-defs-spriteframesprite-properties-hframes.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/hframes")               |
| [name](#name)                      | `string`  | Required | cannot be null | [Proscenio character](proscenio-defs-spriteframesprite-properties-name.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/name")                     |
| [offset](#offset)                  | `array`   | Optional | cannot be null | [Proscenio character](proscenio-defs-spriteframesprite-properties-offset.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/offset")                 |
| [texture](#texture)                | Merged    | Optional | cannot be null | [Proscenio character](proscenio-defs-spriteframesprite-properties-texture.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/texture")               |
| [texture\_region](#texture_region) | Merged    | Optional | cannot be null | [Proscenio character](proscenio-defs-spriteframesprite-properties-texture-region.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/texture_region") |
| [type](#type)                      | `string`  | Required | cannot be null | [Proscenio character](proscenio-defs-spriteframesprite-properties-type.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/type")                     |
| [vframes](#vframes)                | `integer` | Required | cannot be null | [Proscenio character](proscenio-defs-spriteframesprite-properties-vframes.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/vframes")               |

## bone

`bone`

* is required

* Type: `string` ([Bone](proscenio-defs-spriteframesprite-properties-bone.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-spriteframesprite-properties-bone.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/bone")

### bone Type

`string` ([Bone](proscenio-defs-spriteframesprite-properties-bone.md))

## centered

`centered`

* is optional

* Type: `boolean` ([Centered](proscenio-defs-spriteframesprite-properties-centered.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-spriteframesprite-properties-centered.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/centered")

### centered Type

`boolean` ([Centered](proscenio-defs-spriteframesprite-properties-centered.md))

### centered Default Value

The default value is:

```json
true
```

## frame

Initial frame index (row-major). Animation tracks override at runtime.

`frame`

* is optional

* Type: `integer` ([Frame](proscenio-defs-spriteframesprite-properties-frame.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-spriteframesprite-properties-frame.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/frame")

### frame Type

`integer` ([Frame](proscenio-defs-spriteframesprite-properties-frame.md))

### frame Constraints

**minimum**: the value of this number must greater than or equal to: `0`

## hframes

`hframes`

* is required

* Type: `integer` ([Hframes](proscenio-defs-spriteframesprite-properties-hframes.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-spriteframesprite-properties-hframes.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/hframes")

### hframes Type

`integer` ([Hframes](proscenio-defs-spriteframesprite-properties-hframes.md))

### hframes Constraints

**minimum**: the value of this number must greater than or equal to: `1`

## name

`name`

* is required

* Type: `string` ([Name](proscenio-defs-spriteframesprite-properties-name.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-spriteframesprite-properties-name.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/name")

### name Type

`string` ([Name](proscenio-defs-spriteframesprite-properties-name.md))

### name Constraints

**minimum length**: the minimum number of characters for this string is: `1`

## offset

`offset`

* is optional

* Type: `number[]`

* cannot be null

* defined in: [Proscenio character](proscenio-defs-spriteframesprite-properties-offset.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/offset")

### offset Type

`number[]`

### offset Constraints

**maximum number of items**: the maximum number of items for this array is: `2`

**minimum number of items**: the minimum number of items for this array is: `2`

### offset Default Value

The default value is:

```json
[
  0,
  0
]
```

## texture

Optional per-sprite texture filename, resolved relative to the .proscenio document. Mirrors the polygon-sprite field. Importers fall back to the top-level `atlas` field when absent.

`texture`

* is optional

* Type: merged type ([Texture](proscenio-defs-spriteframesprite-properties-texture.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-spriteframesprite-properties-texture.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/texture")

### texture Type

merged type ([Texture](proscenio-defs-spriteframesprite-properties-texture.md))

any of

* [Untitled string in Proscenio character](proscenio-defs-spriteframesprite-properties-texture-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-spriteframesprite-properties-texture-anyof-1.md "check type definition")

## texture\_region

Optional sub-rectangle within the atlas where the spritesheet lives. Absent means use the full atlas.

`texture_region`

* is optional

* Type: merged type ([Texture Region](proscenio-defs-spriteframesprite-properties-texture-region.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-spriteframesprite-properties-texture-region.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/texture_region")

### texture\_region Type

merged type ([Texture Region](proscenio-defs-spriteframesprite-properties-texture-region.md))

any of

* [Untitled array in Proscenio character](proscenio-defs-spriteframesprite-properties-texture-region-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-spriteframesprite-properties-texture-region-anyof-1.md "check type definition")

## type

Discriminator. Required and constant.

`type`

* is required

* Type: `string` ([Type](proscenio-defs-spriteframesprite-properties-type.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-spriteframesprite-properties-type.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/type")

### type Type

`string` ([Type](proscenio-defs-spriteframesprite-properties-type.md))

### type Constraints

**constant**: the value of this property must be equal to:

```json
"sprite_frame"
```

## vframes

`vframes`

* is required

* Type: `integer` ([Vframes](proscenio-defs-spriteframesprite-properties-vframes.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-spriteframesprite-properties-vframes.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/vframes")

### vframes Type

`integer` ([Vframes](proscenio-defs-spriteframesprite-properties-vframes.md))

### vframes Constraints

**minimum**: the value of this number must greater than or equal to: `1`
