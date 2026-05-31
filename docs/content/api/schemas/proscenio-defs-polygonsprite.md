# PolygonSprite Schema

```txt
https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/properties/sprites/items/oneOf/0
```

Cutout-style sprite rendered as a Godot Polygon2D - vertices + UV.

Default sprite kind when `type` is omitted (backwards-compatible
with v1 documents).

Field declaration order mirrors the writer's dict insertion order
so `model_dump_json(exclude_unset=True)` reproduces the golden
fixtures byte-for-byte once the writer migrates.

| Abstract            | Extensible | Status         | Identifiable | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                              |
| :------------------ | :--------- | :------------- | :----------- | :---------------- | :-------------------- | :------------------ | :-------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | No           | Forbidden         | Forbidden             | none                | [proscenio.schema.json\*](../../../../out/proscenio.schema.json "open original schema") |

## 0 Type

`object` ([PolygonSprite](proscenio-defs-polygonsprite.md))

# 0 Properties

| Property                           | Type     | Required | Nullable       | Defined by                                                                                                                                                                                                       |
| :--------------------------------- | :------- | :------- | :------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [bone](#bone)                      | Merged   | Optional | cannot be null | [Proscenio character](proscenio-defs-polygonsprite-properties-bone.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/bone")                     |
| [name](#name)                      | `string` | Required | cannot be null | [Proscenio character](proscenio-defs-polygonsprite-properties-name.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/name")                     |
| [polygon](#polygon)                | `array`  | Required | cannot be null | [Proscenio character](proscenio-defs-polygonsprite-properties-polygon.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/polygon")               |
| [texture](#texture)                | Merged   | Optional | cannot be null | [Proscenio character](proscenio-defs-polygonsprite-properties-texture.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/texture")               |
| [texture\_region](#texture_region) | `array`  | Required | cannot be null | [Proscenio character](proscenio-defs-polygonsprite-properties-texture-region.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/texture_region") |
| [type](#type)                      | `string` | Optional | cannot be null | [Proscenio character](proscenio-defs-polygonsprite-properties-type.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/type")                     |
| [uv](#uv)                          | `array`  | Required | cannot be null | [Proscenio character](proscenio-defs-polygonsprite-properties-uv.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/uv")                         |
| [weights](#weights)                | Merged   | Optional | cannot be null | [Proscenio character](proscenio-defs-polygonsprite-properties-weights.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/weights")               |

## bone



`bone`

* is optional

* Type: merged type ([Bone](proscenio-defs-polygonsprite-properties-bone.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-polygonsprite-properties-bone.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/bone")

### bone Type

merged type ([Bone](proscenio-defs-polygonsprite-properties-bone.md))

any of

* [Untitled string in Proscenio character](proscenio-defs-polygonsprite-properties-bone-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-polygonsprite-properties-bone-anyof-1.md "check type definition")

## name



`name`

* is required

* Type: `string` ([Name](proscenio-defs-polygonsprite-properties-name.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-polygonsprite-properties-name.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/name")

### name Type

`string` ([Name](proscenio-defs-polygonsprite-properties-name.md))

### name Constraints

**minimum length**: the minimum number of characters for this string is: `1`

## polygon



`polygon`

* is required

* Type: `number[][]`

* cannot be null

* defined in: [Proscenio character](proscenio-defs-polygonsprite-properties-polygon.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/polygon")

### polygon Type

`number[][]`

## texture

Optional per-sprite texture filename, resolved relative to the .proscenio document. Multi-PNG fixtures use this so each sprite picks its own image instead of slicing a shared atlas. Importers fall back to the top-level `atlas` field when absent.

`texture`

* is optional

* Type: merged type ([Texture](proscenio-defs-polygonsprite-properties-texture.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-polygonsprite-properties-texture.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/texture")

### texture Type

merged type ([Texture](proscenio-defs-polygonsprite-properties-texture.md))

any of

* [Untitled string in Proscenio character](proscenio-defs-polygonsprite-properties-texture-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-polygonsprite-properties-texture-anyof-1.md "check type definition")

## texture\_region

\[x, y, width, height] in atlas pixels.

`texture_region`

* is required

* Type: `number[]`

* cannot be null

* defined in: [Proscenio character](proscenio-defs-polygonsprite-properties-texture-region.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/texture_region")

### texture\_region Type

`number[]`

### texture\_region Constraints

**maximum number of items**: the maximum number of items for this array is: `4`

**minimum number of items**: the minimum number of items for this array is: `4`

## type

Discriminator. Optional; absence means `polygon`.

`type`

* is optional

* Type: `string` ([Type](proscenio-defs-polygonsprite-properties-type.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-polygonsprite-properties-type.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/type")

### type Type

`string` ([Type](proscenio-defs-polygonsprite-properties-type.md))

### type Constraints

**constant**: the value of this property must be equal to:

```json
"polygon"
```

### type Default Value

The default value is:

```json
"polygon"
```

## uv



`uv`

* is required

* Type: `number[][]`

* cannot be null

* defined in: [Proscenio character](proscenio-defs-polygonsprite-properties-uv.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/uv")

### uv Type

`number[][]`

## weights



`weights`

* is optional

* Type: merged type ([Weights](proscenio-defs-polygonsprite-properties-weights.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-polygonsprite-properties-weights.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/weights")

### weights Type

merged type ([Weights](proscenio-defs-polygonsprite-properties-weights.md))

any of

* [Untitled array in Proscenio character](proscenio-defs-polygonsprite-properties-weights-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-polygonsprite-properties-weights-anyof-1.md "check type definition")
