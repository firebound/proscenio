# SpriteFrameLayer Schema

```txt
https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/properties/layers/items/oneOf/1
```

N frames, single quad mesh, animated via `proscenio.frame`.

Authored as a LayerSet tagged `[spritesheet]`.

| Abstract            | Extensible | Status         | Identifiable | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                                     |
| :------------------ | :--------- | :------------- | :----------- | :---------------- | :-------------------- | :------------------ | :--------------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | No           | Forbidden         | Forbidden             | none                | [psd\_manifest.schema.json\*](../../../../out/psd_manifest.schema.json "open original schema") |

## 1 Type

`object` ([SpriteFrameLayer](psd_manifest-defs-spriteframelayer.md))

# 1 Properties

| Property                   | Type      | Required | Nullable       | Defined by                                                                                                                                                                                                              |
| :------------------------- | :-------- | :------- | :------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [blend\_mode](#blend_mode) | Merged    | Optional | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-blend-mode.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/blend_mode") |
| [frames](#frames)          | `array`   | Required | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-frames.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/frames")         |
| [kind](#kind)              | `string`  | Required | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-kind.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/kind")             |
| [name](#name)              | `string`  | Required | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-name.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/name")             |
| [origin](#origin)          | Merged    | Optional | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-origin.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/origin")         |
| [position](#position)      | `array`   | Required | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-position.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/position")     |
| [size](#size)              | `array`   | Required | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-size.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/size")             |
| [subfolder](#subfolder)    | Merged    | Optional | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-subfolder.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/subfolder")   |
| [z\_order](#z_order)       | `integer` | Required | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-z-order.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/z_order")       |

## blend\_mode



`blend_mode`

* is optional

* Type: merged type ([Blend Mode](psd_manifest-defs-spriteframelayer-properties-blend-mode.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-blend-mode.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/blend_mode")

### blend\_mode Type

merged type ([Blend Mode](psd_manifest-defs-spriteframelayer-properties-blend-mode.md))

any of

* [Untitled string in Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-blend-mode-anyof-0.md "check type definition")

* [Untitled null in Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-blend-mode-anyof-1.md "check type definition")

## frames



`frames`

* is required

* Type: `object[]` ([FrameEntry](psd_manifest-defs-frameentry.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-frames.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/frames")

### frames Type

`object[]` ([FrameEntry](psd_manifest-defs-frameentry.md))

### frames Constraints

**minimum number of items**: the minimum number of items for this array is: `2`

## kind



`kind`

* is required

* Type: `string` ([Kind](psd_manifest-defs-spriteframelayer-properties-kind.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-kind.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/kind")

### kind Type

`string` ([Kind](psd_manifest-defs-spriteframelayer-properties-kind.md))

### kind Constraints

**constant**: the value of this property must be equal to:

```json
"sprite_frame"
```

## name



`name`

* is required

* Type: `string` ([Name](psd_manifest-defs-spriteframelayer-properties-name.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-name.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/name")

### name Type

`string` ([Name](psd_manifest-defs-spriteframelayer-properties-name.md))

### name Constraints

**minimum length**: the minimum number of characters for this string is: `1`

## origin

Optional pivot in PSD pixels (see polygon\_layer.origin).

`origin`

* is optional

* Type: merged type ([Origin](psd_manifest-defs-spriteframelayer-properties-origin.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-origin.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/origin")

### origin Type

merged type ([Origin](psd_manifest-defs-spriteframelayer-properties-origin.md))

any of

* [Untitled array in Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-origin-anyof-0.md "check type definition")

* [Untitled null in Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-origin-anyof-1.md "check type definition")

## position

PSD top-left bbox of the largest frame.

`position`

* is required

* Type: `integer[]`

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-position.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/position")

### position Type

`integer[]`

### position Constraints

**maximum number of items**: the maximum number of items for this array is: `2`

**minimum number of items**: the minimum number of items for this array is: `2`

## size

Largest frame bbox size in pixels (importer pads smaller frames to match).

`size`

* is required

* Type: `integer[]`

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-size.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/size")

### size Type

`integer[]`

### size Constraints

**maximum number of items**: the maximum number of items for this array is: `2`

**minimum number of items**: the minimum number of items for this array is: `2`

## subfolder



`subfolder`

* is optional

* Type: merged type ([Subfolder](psd_manifest-defs-spriteframelayer-properties-subfolder.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-subfolder.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/subfolder")

### subfolder Type

merged type ([Subfolder](psd_manifest-defs-spriteframelayer-properties-subfolder.md))

any of

* [Untitled string in Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-subfolder-anyof-0.md "check type definition")

* [Untitled null in Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-subfolder-anyof-1.md "check type definition")

## z\_order



`z_order`

* is required

* Type: `integer` ([Z Order](psd_manifest-defs-spriteframelayer-properties-z-order.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-spriteframelayer-properties-z-order.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/z_order")

### z\_order Type

`integer` ([Z Order](psd_manifest-defs-spriteframelayer-properties-z-order.md))

### z\_order Constraints

**minimum**: the value of this number must greater than or equal to: `0`
