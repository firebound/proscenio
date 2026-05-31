# Proscenio PSD manifest Schema

```txt
https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json
```

Root of a PSD manifest v2 document.

| Abstract            | Extensible | Status         | Identifiable | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                                   |
| :------------------ | :--------- | :------------- | :----------- | :---------------- | :-------------------- | :------------------ | :------------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | No           | Forbidden         | Forbidden             | none                | [psd\_manifest.schema.json](../../../../out/psd_manifest.schema.json "open original schema") |

## Proscenio PSD manifest Type

`object` ([Proscenio PSD manifest](psd_manifest.md))

# Proscenio PSD manifest Properties

| Property                              | Type      | Required | Nullable       | Defined by                                                                                                                                                                           |
| :------------------------------------ | :-------- | :------- | :------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [anchor](#anchor)                     | Merged    | Optional | cannot be null | [Proscenio PSD manifest](psd_manifest-properties-anchor.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/properties/anchor")                   |
| [doc](#doc)                           | `string`  | Required | cannot be null | [Proscenio PSD manifest](psd_manifest-properties-doc.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/properties/doc")                         |
| [format\_version](#format_version)    | `integer` | Required | cannot be null | [Proscenio PSD manifest](psd_manifest-properties-format-version.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/properties/format_version")   |
| [layers](#layers)                     | `array`   | Required | cannot be null | [Proscenio PSD manifest](psd_manifest-properties-layers.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/properties/layers")                   |
| [pixels\_per\_unit](#pixels_per_unit) | `number`  | Required | cannot be null | [Proscenio PSD manifest](psd_manifest-properties-pixels-per-unit.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/properties/pixels_per_unit") |
| [size](#size)                         | `array`   | Required | cannot be null | [Proscenio PSD manifest](psd_manifest-properties-size.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/properties/size")                       |

## anchor

Document anchor in PSD pixels. Set by the first horizontal + vertical PSD guide; importer places the root bone here. Omitted when no guides were authored.

`anchor`

* is optional

* Type: merged type ([Anchor](psd_manifest-properties-anchor.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-properties-anchor.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/properties/anchor")

### anchor Type

merged type ([Anchor](psd_manifest-properties-anchor.md))

any of

* [Untitled array in Proscenio PSD manifest](psd_manifest-properties-anchor-anyof-0.md "check type definition")

* [Untitled null in Proscenio PSD manifest](psd_manifest-properties-anchor-anyof-1.md "check type definition")

## doc

Original PSD filename. Display only - not a resolvable path.

`doc`

* is required

* Type: `string` ([Doc](psd_manifest-properties-doc.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-properties-doc.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/properties/doc")

### doc Type

`string` ([Doc](psd_manifest-properties-doc.md))

### doc Constraints

**minimum length**: the minimum number of characters for this string is: `1`

## format\_version

Bump on any breaking change to the shape of this document. v2 introduces the tag-driven taxonomy in the photoshop tag system (anchor, per-entry origin, blend\_mode, subfolder, kind: "mesh").

`format_version`

* is required

* Type: `integer` ([Format Version](psd_manifest-properties-format-version.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-properties-format-version.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/properties/format_version")

### format\_version Type

`integer` ([Format Version](psd_manifest-properties-format-version.md))

### format\_version Constraints

**constant**: the value of this property must be equal to:

```json
2
```

## layers

Z-ordered top-to-bottom. Each entry is a single mesh in Blender after import.

`layers`

* is required

* Type: an array of merged types ([Details](psd_manifest-properties-layers-items.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-properties-layers.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/properties/layers")

### layers Type

an array of merged types ([Details](psd_manifest-properties-layers-items.md))

## pixels\_per\_unit

Importer divides PSD pixels by this when stamping mesh size and position.

`pixels_per_unit`

* is required

* Type: `number` ([Pixels Per Unit](psd_manifest-properties-pixels-per-unit.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-properties-pixels-per-unit.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/properties/pixels_per_unit")

### pixels\_per\_unit Type

`number` ([Pixels Per Unit](psd_manifest-properties-pixels-per-unit.md))

### pixels\_per\_unit Constraints

**minimum (exclusive)**: the value of this number must be greater than: `0`

## size

\[doc\_width\_px, doc\_height\_px].

`size`

* is required

* Type: `integer[]`

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-properties-size.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/properties/size")

### size Type

`integer[]`

### size Constraints

**maximum number of items**: the maximum number of items for this array is: `2`

**minimum number of items**: the minimum number of items for this array is: `2`

# Proscenio PSD manifest Definitions

## Definitions group FrameEntry

Reference this group by using

```json
{"$ref":"https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/FrameEntry"}
```

| Property        | Type      | Required | Nullable       | Defined by                                                                                                                                                                                        |
| :-------------- | :-------- | :------- | :------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [index](#index) | `integer` | Required | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-frameentry-properties-index.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/FrameEntry/properties/index") |
| [path](#path)   | `string`  | Required | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-frameentry-properties-path.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/FrameEntry/properties/path")   |

### index

Frame index, 0-based, contiguous, ordered.

`index`

* is required

* Type: `integer` ([Index](psd_manifest-defs-frameentry-properties-index.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-frameentry-properties-index.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/FrameEntry/properties/index")

#### index Type

`integer` ([Index](psd_manifest-defs-frameentry-properties-index.md))

#### index Constraints

**minimum**: the value of this number must greater than or equal to: `0`

### path

Path to the frame PNG, relative to the manifest file.

`path`

* is required

* Type: `string` ([Path](psd_manifest-defs-frameentry-properties-path.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-frameentry-properties-path.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/FrameEntry/properties/path")

#### path Type

`string` ([Path](psd_manifest-defs-frameentry-properties-path.md))

#### path Constraints

**minimum length**: the minimum number of characters for this string is: `1`

## Definitions group PolygonLayer

Reference this group by using

```json
{"$ref":"https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer"}
```

| Property                   | Type      | Required | Nullable       | Defined by                                                                                                                                                                                                      |
| :------------------------- | :-------- | :------- | :------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [blend\_mode](#blend_mode) | Merged    | Optional | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-blend-mode.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/blend_mode") |
| [kind](#kind)              | `string`  | Required | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-kind.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/kind")             |
| [name](#name)              | `string`  | Required | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-name.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/name")             |
| [origin](#origin)          | Merged    | Optional | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-origin.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/origin")         |
| [path](#path-1)            | `string`  | Required | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-path.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/path")             |
| [position](#position)      | `array`   | Required | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-position.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/position")     |
| [size](#size-1)            | `array`   | Required | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-size.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/size")             |
| [subfolder](#subfolder)    | Merged    | Optional | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-subfolder.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/subfolder")   |
| [z\_order](#z_order)       | `integer` | Required | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-z-order.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/z_order")       |

### blend\_mode

Layer blend mode emitted from the PSD; importer maps to material blend mode.

`blend_mode`

* is optional

* Type: merged type ([Blend Mode](psd_manifest-defs-polygonlayer-properties-blend-mode.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-blend-mode.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/blend_mode")

#### blend\_mode Type

merged type ([Blend Mode](psd_manifest-defs-polygonlayer-properties-blend-mode.md))

any of

* [Untitled string in Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-blend-mode-anyof-0.md "check type definition")

* [Untitled null in Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-blend-mode-anyof-1.md "check type definition")

### kind



`kind`

* is required

* Type: `string` ([Kind](psd_manifest-defs-polygonlayer-properties-kind.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-kind.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/kind")

#### kind Type

`string` ([Kind](psd_manifest-defs-polygonlayer-properties-kind.md))

#### kind Constraints

**enum**: the value of this property must be equal to one of the following values:

| Value       | Explanation |
| :---------- | :---------- |
| `"polygon"` |             |
| `"mesh"`    |             |

### name



`name`

* is required

* Type: `string` ([Name](psd_manifest-defs-polygonlayer-properties-name.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-name.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/name")

#### name Type

`string` ([Name](psd_manifest-defs-polygonlayer-properties-name.md))

#### name Constraints

**minimum length**: the minimum number of characters for this string is: `1`

### origin

Optional pivot in PSD pixels. Set by the \[origin:x,y] tag or by an \[origin] marker layer inside the group. Importer uses this as the mesh's Object.location when present; falls back to bbox center otherwise.

`origin`

* is optional

* Type: merged type ([Origin](psd_manifest-defs-polygonlayer-properties-origin.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-origin.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/origin")

#### origin Type

merged type ([Origin](psd_manifest-defs-polygonlayer-properties-origin.md))

any of

* [Untitled array in Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-origin-anyof-0.md "check type definition")

* [Untitled null in Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-origin-anyof-1.md "check type definition")

### path

Path to the layer PNG, relative to the manifest file.

`path`

* is required

* Type: `string` ([Path](psd_manifest-defs-polygonlayer-properties-path.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-path.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/path")

#### path Type

`string` ([Path](psd_manifest-defs-polygonlayer-properties-path.md))

#### path Constraints

**minimum length**: the minimum number of characters for this string is: `1`

### position

PSD top-left bbox of the layer in pixels.

`position`

* is required

* Type: `integer[]`

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-position.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/position")

#### position Type

`integer[]`

#### position Constraints

**maximum number of items**: the maximum number of items for this array is: `2`

**minimum number of items**: the minimum number of items for this array is: `2`

### size

Layer bbox size in pixels.

`size`

* is required

* Type: `integer[]`

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-size.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/size")

#### size Type

`integer[]`

#### size Constraints

**maximum number of items**: the maximum number of items for this array is: `2`

**minimum number of items**: the minimum number of items for this array is: `2`

### subfolder

Optional output sub-folder under images/, set by the \[folder:name] tag. Importer ignores; this is purely a disk-layout hint reflected in `path`.

`subfolder`

* is optional

* Type: merged type ([Subfolder](psd_manifest-defs-polygonlayer-properties-subfolder.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-subfolder.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/subfolder")

#### subfolder Type

merged type ([Subfolder](psd_manifest-defs-polygonlayer-properties-subfolder.md))

any of

* [Untitled string in Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-subfolder-anyof-0.md "check type definition")

* [Untitled null in Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-subfolder-anyof-1.md "check type definition")

### z\_order

Stack index, 0 = top.

`z_order`

* is required

* Type: `integer` ([Z Order](psd_manifest-defs-polygonlayer-properties-z-order.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-z-order.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/z_order")

#### z\_order Type

`integer` ([Z Order](psd_manifest-defs-polygonlayer-properties-z-order.md))

#### z\_order Constraints

**minimum**: the value of this number must greater than or equal to: `0`

## Definitions group SpriteFrameLayer

Reference this group by using

```json
{"$ref":"https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer"}
```

| Property                     | Type      | Required | Nullable       | Defined by                                                                                                                                                                                                              |
| :--------------------------- | :-------- | :------- | :------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [blend\_mode](#blend_mode-1) | Merged    | Optional | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-blend-mode.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/blend_mode") |
| [frames](#frames)            | `array`   | Required | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-frames.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/frames")         |
| [kind](#kind-1)              | `string`  | Required | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-kind.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/kind")             |
| [name](#name-1)              | `string`  | Required | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-name.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/name")             |
| [origin](#origin-1)          | Merged    | Optional | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-origin.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/origin")         |
| [position](#position-1)      | `array`   | Required | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-position.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/position")     |
| [size](#size-2)              | `array`   | Required | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-size.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/size")             |
| [subfolder](#subfolder-1)    | Merged    | Optional | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-subfolder.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/subfolder")   |
| [z\_order](#z_order-1)       | `integer` | Required | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-z-order.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/z_order")       |

### blend\_mode



`blend_mode`

* is optional

* Type: merged type ([Blend Mode](psd_manifest-defs-spriteframelayer-properties-blend-mode.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-blend-mode.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/blend_mode")

#### blend\_mode Type

merged type ([Blend Mode](psd_manifest-defs-spriteframelayer-properties-blend-mode.md))

any of

* [Untitled string in Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-blend-mode-anyof-0.md "check type definition")

* [Untitled null in Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-blend-mode-anyof-1.md "check type definition")

### frames



`frames`

* is required

* Type: `object[]` ([FrameEntry](psd_manifest-defs-frameentry.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-frames.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/frames")

#### frames Type

`object[]` ([FrameEntry](psd_manifest-defs-frameentry.md))

#### frames Constraints

**minimum number of items**: the minimum number of items for this array is: `2`

### kind



`kind`

* is required

* Type: `string` ([Kind](psd_manifest-defs-spriteframelayer-properties-kind.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-kind.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/kind")

#### kind Type

`string` ([Kind](psd_manifest-defs-spriteframelayer-properties-kind.md))

#### kind Constraints

**constant**: the value of this property must be equal to:

```json
"sprite_frame"
```

### name



`name`

* is required

* Type: `string` ([Name](psd_manifest-defs-spriteframelayer-properties-name.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-name.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/name")

#### name Type

`string` ([Name](psd_manifest-defs-spriteframelayer-properties-name.md))

#### name Constraints

**minimum length**: the minimum number of characters for this string is: `1`

### origin

Optional pivot in PSD pixels (see polygon\_layer.origin).

`origin`

* is optional

* Type: merged type ([Origin](psd_manifest-defs-spriteframelayer-properties-origin.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-origin.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/origin")

#### origin Type

merged type ([Origin](psd_manifest-defs-spriteframelayer-properties-origin.md))

any of

* [Untitled array in Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-origin-anyof-0.md "check type definition")

* [Untitled null in Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-origin-anyof-1.md "check type definition")

### position

PSD top-left bbox of the largest frame.

`position`

* is required

* Type: `integer[]`

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-position.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/position")

#### position Type

`integer[]`

#### position Constraints

**maximum number of items**: the maximum number of items for this array is: `2`

**minimum number of items**: the minimum number of items for this array is: `2`

### size

Largest frame bbox size in pixels (importer pads smaller frames to match).

`size`

* is required

* Type: `integer[]`

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-size.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/size")

#### size Type

`integer[]`

#### size Constraints

**maximum number of items**: the maximum number of items for this array is: `2`

**minimum number of items**: the minimum number of items for this array is: `2`

### subfolder



`subfolder`

* is optional

* Type: merged type ([Subfolder](psd_manifest-defs-spriteframelayer-properties-subfolder.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-subfolder.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/subfolder")

#### subfolder Type

merged type ([Subfolder](psd_manifest-defs-spriteframelayer-properties-subfolder.md))

any of

* [Untitled string in Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-subfolder-anyof-0.md "check type definition")

* [Untitled null in Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-subfolder-anyof-1.md "check type definition")

### z\_order



`z_order`

* is required

* Type: `integer` ([Z Order](psd_manifest-defs-spriteframelayer-properties-z-order.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-z-order.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/z_order")

#### z\_order Type

`integer` ([Z Order](psd_manifest-defs-spriteframelayer-properties-z-order.md))

#### z\_order Constraints

**minimum**: the value of this number must greater than or equal to: `0`
