# Proscenio character Schema

```txt
https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json
```

Root of a .proscenio v1 document.

Schema id mirrors the hand-maintained file so consumer ajv
validators that key off `$id` continue to resolve.

| Abstract            | Extensible | Status         | Identifiable | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                            |
| :------------------ | :--------- | :------------- | :----------- | :---------------- | :-------------------- | :------------------ | :------------------------------------------------------------------------------------ |
| Can be instantiated | No         | Unknown status | No           | Forbidden         | Forbidden             | none                | [proscenio.schema.json](../../../../out/proscenio.schema.json "open original schema") |

## Proscenio character Type

`object` ([Proscenio character](proscenio.md))

# Proscenio character Properties

| Property                              | Type      | Required | Nullable       | Defined by                                                                                                                                                                  |
| :------------------------------------ | :-------- | :------- | :------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [animations](#animations)             | Merged    | Optional | cannot be null | [Proscenio character](proscenio-properties-animations.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/properties/animations")           |
| [atlas](#atlas)                       | Merged    | Optional | cannot be null | [Proscenio character](proscenio-properties-atlas.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/properties/atlas")                     |
| [format\_version](#format_version)    | `integer` | Required | cannot be null | [Proscenio character](proscenio-properties-format-version.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/properties/format_version")   |
| [name](#name)                         | `string`  | Required | cannot be null | [Proscenio character](proscenio-properties-name.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/properties/name")                       |
| [pixels\_per\_unit](#pixels_per_unit) | `number`  | Required | cannot be null | [Proscenio character](proscenio-properties-pixels-per-unit.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/properties/pixels_per_unit") |
| [skeleton](#skeleton)                 | `object`  | Required | cannot be null | [Proscenio character](proscenio-defs-skeleton.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/properties/skeleton")                     |
| [slots](#slots)                       | Merged    | Optional | cannot be null | [Proscenio character](proscenio-properties-slots.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/properties/slots")                     |
| [sprites](#sprites)                   | `array`   | Required | cannot be null | [Proscenio character](proscenio-properties-sprites.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/properties/sprites")                 |

## animations



`animations`

* is optional

* Type: merged type ([Animations](proscenio-properties-animations.md))

* cannot be null

* defined in: [Proscenio character](proscenio-properties-animations.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/properties/animations")

### animations Type

merged type ([Animations](proscenio-properties-animations.md))

any of

* [Untitled array in Proscenio character](proscenio-properties-animations-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-properties-animations-anyof-1.md "check type definition")

## atlas



`atlas`

* is optional

* Type: merged type ([Atlas](proscenio-properties-atlas.md))

* cannot be null

* defined in: [Proscenio character](proscenio-properties-atlas.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/properties/atlas")

### atlas Type

merged type ([Atlas](proscenio-properties-atlas.md))

any of

* [Untitled string in Proscenio character](proscenio-properties-atlas-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-properties-atlas-anyof-1.md "check type definition")

## format\_version

Bump on any breaking change to the shape of this document.

`format_version`

* is required

* Type: `integer` ([Format Version](proscenio-properties-format-version.md))

* cannot be null

* defined in: [Proscenio character](proscenio-properties-format-version.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/properties/format_version")

### format\_version Type

`integer` ([Format Version](proscenio-properties-format-version.md))

### format\_version Constraints

**constant**: the value of this property must be equal to:

```json
1
```

## name



`name`

* is required

* Type: `string` ([Name](proscenio-properties-name.md))

* cannot be null

* defined in: [Proscenio character](proscenio-properties-name.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/properties/name")

### name Type

`string` ([Name](proscenio-properties-name.md))

### name Constraints

**minimum length**: the minimum number of characters for this string is: `1`

## pixels\_per\_unit



`pixels_per_unit`

* is required

* Type: `number` ([Pixels Per Unit](proscenio-properties-pixels-per-unit.md))

* cannot be null

* defined in: [Proscenio character](proscenio-properties-pixels-per-unit.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/properties/pixels_per_unit")

### pixels\_per\_unit Type

`number` ([Pixels Per Unit](proscenio-properties-pixels-per-unit.md))

### pixels\_per\_unit Constraints

**minimum (exclusive)**: the value of this number must be greater than: `0`

## skeleton



`skeleton`

* is required

* Type: `object` ([Skeleton](proscenio-defs-skeleton.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-skeleton.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/properties/skeleton")

### skeleton Type

`object` ([Skeleton](proscenio-defs-skeleton.md))

## slots



`slots`

* is optional

* Type: merged type ([Slots](proscenio-properties-slots.md))

* cannot be null

* defined in: [Proscenio character](proscenio-properties-slots.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/properties/slots")

### slots Type

merged type ([Slots](proscenio-properties-slots.md))

any of

* [Untitled array in Proscenio character](proscenio-properties-slots-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-properties-slots-anyof-1.md "check type definition")

## sprites



`sprites`

* is required

* Type: an array of merged types ([Details](proscenio-properties-sprites-items.md))

* cannot be null

* defined in: [Proscenio character](proscenio-properties-sprites.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/properties/sprites")

### sprites Type

an array of merged types ([Details](proscenio-properties-sprites-items.md))

# Proscenio character Definitions

## Definitions group Animation

Reference this group by using

```json
{"$ref":"https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Animation"}
```

| Property          | Type     | Required | Nullable       | Defined by                                                                                                                                                                               |
| :---------------- | :------- | :------- | :------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [length](#length) | `number` | Required | cannot be null | [Proscenio character](proscenio-defs-animation-properties-length.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Animation/properties/length") |
| [loop](#loop)     | Merged   | Optional | cannot be null | [Proscenio character](proscenio-defs-animation-properties-loop.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Animation/properties/loop")     |
| [name](#name-1)   | `string` | Required | cannot be null | [Proscenio character](proscenio-defs-animation-properties-name.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Animation/properties/name")     |
| [tracks](#tracks) | `array`  | Required | cannot be null | [Proscenio character](proscenio-defs-animation-properties-tracks.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Animation/properties/tracks") |

### length



`length`

* is required

* Type: `number` ([Length](proscenio-defs-animation-properties-length.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-animation-properties-length.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Animation/properties/length")

#### length Type

`number` ([Length](proscenio-defs-animation-properties-length.md))

#### length Constraints

**minimum (exclusive)**: the value of this number must be greater than: `0`

### loop



`loop`

* is optional

* Type: merged type ([Loop](proscenio-defs-animation-properties-loop.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-animation-properties-loop.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Animation/properties/loop")

#### loop Type

merged type ([Loop](proscenio-defs-animation-properties-loop.md))

any of

* [Untitled boolean in Proscenio character](proscenio-defs-animation-properties-loop-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-animation-properties-loop-anyof-1.md "check type definition")

### name



`name`

* is required

* Type: `string` ([Name](proscenio-defs-animation-properties-name.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-animation-properties-name.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Animation/properties/name")

#### name Type

`string` ([Name](proscenio-defs-animation-properties-name.md))

#### name Constraints

**minimum length**: the minimum number of characters for this string is: `1`

### tracks



`tracks`

* is required

* Type: `object[]` ([Track](proscenio-defs-track.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-animation-properties-tracks.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Animation/properties/tracks")

#### tracks Type

`object[]` ([Track](proscenio-defs-track.md))

## Definitions group Bone

Reference this group by using

```json
{"$ref":"https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Bone"}
```

| Property              | Type     | Required | Nullable       | Defined by                                                                                                                                                                         |
| :-------------------- | :------- | :------- | :------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [length](#length-1)   | Merged   | Optional | cannot be null | [Proscenio character](proscenio-defs-bone-properties-length.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Bone/properties/length")     |
| [name](#name-2)       | `string` | Required | cannot be null | [Proscenio character](proscenio-defs-bone-properties-name.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Bone/properties/name")         |
| [parent](#parent)     | Merged   | Optional | cannot be null | [Proscenio character](proscenio-defs-bone-properties-parent.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Bone/properties/parent")     |
| [position](#position) | Merged   | Optional | cannot be null | [Proscenio character](proscenio-defs-bone-properties-position.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Bone/properties/position") |
| [rotation](#rotation) | Merged   | Optional | cannot be null | [Proscenio character](proscenio-defs-bone-properties-rotation.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Bone/properties/rotation") |
| [scale](#scale)       | Merged   | Optional | cannot be null | [Proscenio character](proscenio-defs-bone-properties-scale.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Bone/properties/scale")       |

### length



`length`

* is optional

* Type: merged type ([Length](proscenio-defs-bone-properties-length.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-bone-properties-length.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Bone/properties/length")

#### length Type

merged type ([Length](proscenio-defs-bone-properties-length.md))

any of

* [Untitled number in Proscenio character](proscenio-defs-bone-properties-length-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-bone-properties-length-anyof-1.md "check type definition")

### name



`name`

* is required

* Type: `string` ([Name](proscenio-defs-bone-properties-name.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-bone-properties-name.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Bone/properties/name")

#### name Type

`string` ([Name](proscenio-defs-bone-properties-name.md))

#### name Constraints

**minimum length**: the minimum number of characters for this string is: `1`

### parent



`parent`

* is optional

* Type: merged type ([Parent](proscenio-defs-bone-properties-parent.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-bone-properties-parent.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Bone/properties/parent")

#### parent Type

merged type ([Parent](proscenio-defs-bone-properties-parent.md))

any of

* [Untitled string in Proscenio character](proscenio-defs-bone-properties-parent-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-bone-properties-parent-anyof-1.md "check type definition")

### position



`position`

* is optional

* Type: merged type ([Position](proscenio-defs-bone-properties-position.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-bone-properties-position.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Bone/properties/position")

#### position Type

merged type ([Position](proscenio-defs-bone-properties-position.md))

any of

* [Untitled array in Proscenio character](proscenio-defs-bone-properties-position-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-bone-properties-position-anyof-1.md "check type definition")

### rotation



`rotation`

* is optional

* Type: merged type ([Rotation](proscenio-defs-bone-properties-rotation.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-bone-properties-rotation.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Bone/properties/rotation")

#### rotation Type

merged type ([Rotation](proscenio-defs-bone-properties-rotation.md))

any of

* [Untitled number in Proscenio character](proscenio-defs-bone-properties-rotation-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-bone-properties-rotation-anyof-1.md "check type definition")

### scale



`scale`

* is optional

* Type: merged type ([Scale](proscenio-defs-bone-properties-scale.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-bone-properties-scale.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Bone/properties/scale")

#### scale Type

merged type ([Scale](proscenio-defs-bone-properties-scale.md))

any of

* [Untitled array in Proscenio character](proscenio-defs-bone-properties-scale-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-bone-properties-scale-anyof-1.md "check type definition")

## Definitions group Key

Reference this group by using

```json
{"$ref":"https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Key"}
```

| Property                  | Type     | Required | Nullable       | Defined by                                                                                                                                                                           |
| :------------------------ | :------- | :------- | :------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [attachment](#attachment) | Merged   | Optional | cannot be null | [Proscenio character](proscenio-defs-key-properties-attachment.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Key/properties/attachment") |
| [frame](#frame)           | Merged   | Optional | cannot be null | [Proscenio character](proscenio-defs-key-properties-frame.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Key/properties/frame")           |
| [interp](#interp)         | Merged   | Optional | cannot be null | [Proscenio character](proscenio-defs-key-properties-interp.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Key/properties/interp")         |
| [position](#position-1)   | Merged   | Optional | cannot be null | [Proscenio character](proscenio-defs-key-properties-position.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Key/properties/position")     |
| [rotation](#rotation-1)   | Merged   | Optional | cannot be null | [Proscenio character](proscenio-defs-key-properties-rotation.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Key/properties/rotation")     |
| [scale](#scale-1)         | Merged   | Optional | cannot be null | [Proscenio character](proscenio-defs-key-properties-scale.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Key/properties/scale")           |
| [time](#time)             | `number` | Required | cannot be null | [Proscenio character](proscenio-defs-key-properties-time.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Key/properties/time")             |
| [visible](#visible)       | Merged   | Optional | cannot be null | [Proscenio character](proscenio-defs-key-properties-visible.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Key/properties/visible")       |

### attachment



`attachment`

* is optional

* Type: merged type ([Attachment](proscenio-defs-key-properties-attachment.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-key-properties-attachment.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Key/properties/attachment")

#### attachment Type

merged type ([Attachment](proscenio-defs-key-properties-attachment.md))

any of

* [Untitled string in Proscenio character](proscenio-defs-key-properties-attachment-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-key-properties-attachment-anyof-1.md "check type definition")

### frame



`frame`

* is optional

* Type: merged type ([Frame](proscenio-defs-key-properties-frame.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-key-properties-frame.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Key/properties/frame")

#### frame Type

merged type ([Frame](proscenio-defs-key-properties-frame.md))

any of

* [Untitled integer in Proscenio character](proscenio-defs-key-properties-frame-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-key-properties-frame-anyof-1.md "check type definition")

### interp



`interp`

* is optional

* Type: merged type ([Interp](proscenio-defs-key-properties-interp.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-key-properties-interp.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Key/properties/interp")

#### interp Type

merged type ([Interp](proscenio-defs-key-properties-interp.md))

any of

* [Untitled string in Proscenio character](proscenio-defs-key-properties-interp-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-key-properties-interp-anyof-1.md "check type definition")

### position



`position`

* is optional

* Type: merged type ([Position](proscenio-defs-key-properties-position.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-key-properties-position.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Key/properties/position")

#### position Type

merged type ([Position](proscenio-defs-key-properties-position.md))

any of

* [Untitled array in Proscenio character](proscenio-defs-key-properties-position-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-key-properties-position-anyof-1.md "check type definition")

### rotation



`rotation`

* is optional

* Type: merged type ([Rotation](proscenio-defs-key-properties-rotation.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-key-properties-rotation.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Key/properties/rotation")

#### rotation Type

merged type ([Rotation](proscenio-defs-key-properties-rotation.md))

any of

* [Untitled number in Proscenio character](proscenio-defs-key-properties-rotation-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-key-properties-rotation-anyof-1.md "check type definition")

### scale



`scale`

* is optional

* Type: merged type ([Scale](proscenio-defs-key-properties-scale.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-key-properties-scale.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Key/properties/scale")

#### scale Type

merged type ([Scale](proscenio-defs-key-properties-scale.md))

any of

* [Untitled array in Proscenio character](proscenio-defs-key-properties-scale-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-key-properties-scale-anyof-1.md "check type definition")

### time



`time`

* is required

* Type: `number` ([Time](proscenio-defs-key-properties-time.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-key-properties-time.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Key/properties/time")

#### time Type

`number` ([Time](proscenio-defs-key-properties-time.md))

#### time Constraints

**minimum**: the value of this number must greater than or equal to: `0`

### visible



`visible`

* is optional

* Type: merged type ([Visible](proscenio-defs-key-properties-visible.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-key-properties-visible.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Key/properties/visible")

#### visible Type

merged type ([Visible](proscenio-defs-key-properties-visible.md))

any of

* [Untitled boolean in Proscenio character](proscenio-defs-key-properties-visible-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-key-properties-visible-anyof-1.md "check type definition")

## Definitions group PolygonSprite

Reference this group by using

```json
{"$ref":"https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite"}
```

| Property                           | Type     | Required | Nullable       | Defined by                                                                                                                                                                                                       |
| :--------------------------------- | :------- | :------- | :------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [bone](#bone)                      | Merged   | Optional | cannot be null | [Proscenio character](proscenio-defs-polygonsprite-properties-bone.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/bone")                     |
| [name](#name-3)                    | `string` | Required | cannot be null | [Proscenio character](proscenio-defs-polygonsprite-properties-name.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/name")                     |
| [polygon](#polygon)                | `array`  | Required | cannot be null | [Proscenio character](proscenio-defs-polygonsprite-properties-polygon.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/polygon")               |
| [texture](#texture)                | Merged   | Optional | cannot be null | [Proscenio character](proscenio-defs-polygonsprite-properties-texture.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/texture")               |
| [texture\_region](#texture_region) | `array`  | Required | cannot be null | [Proscenio character](proscenio-defs-polygonsprite-properties-texture-region.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/texture_region") |
| [type](#type)                      | `string` | Optional | cannot be null | [Proscenio character](proscenio-defs-polygonsprite-properties-type.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/type")                     |
| [uv](#uv)                          | `array`  | Required | cannot be null | [Proscenio character](proscenio-defs-polygonsprite-properties-uv.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/uv")                         |
| [weights](#weights)                | Merged   | Optional | cannot be null | [Proscenio character](proscenio-defs-polygonsprite-properties-weights.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/weights")               |

### bone



`bone`

* is optional

* Type: merged type ([Bone](proscenio-defs-polygonsprite-properties-bone.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-polygonsprite-properties-bone.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/bone")

#### bone Type

merged type ([Bone](proscenio-defs-polygonsprite-properties-bone.md))

any of

* [Untitled string in Proscenio character](proscenio-defs-polygonsprite-properties-bone-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-polygonsprite-properties-bone-anyof-1.md "check type definition")

### name



`name`

* is required

* Type: `string` ([Name](proscenio-defs-polygonsprite-properties-name.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-polygonsprite-properties-name.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/name")

#### name Type

`string` ([Name](proscenio-defs-polygonsprite-properties-name.md))

#### name Constraints

**minimum length**: the minimum number of characters for this string is: `1`

### polygon



`polygon`

* is required

* Type: `number[][]`

* cannot be null

* defined in: [Proscenio character](proscenio-defs-polygonsprite-properties-polygon.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/polygon")

#### polygon Type

`number[][]`

### texture

Optional per-sprite texture filename, resolved relative to the .proscenio document. Multi-PNG fixtures use this so each sprite picks its own image instead of slicing a shared atlas. Importers fall back to the top-level `atlas` field when absent.

`texture`

* is optional

* Type: merged type ([Texture](proscenio-defs-polygonsprite-properties-texture.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-polygonsprite-properties-texture.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/texture")

#### texture Type

merged type ([Texture](proscenio-defs-polygonsprite-properties-texture.md))

any of

* [Untitled string in Proscenio character](proscenio-defs-polygonsprite-properties-texture-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-polygonsprite-properties-texture-anyof-1.md "check type definition")

### texture\_region

\[x, y, width, height] in atlas pixels.

`texture_region`

* is required

* Type: `number[]`

* cannot be null

* defined in: [Proscenio character](proscenio-defs-polygonsprite-properties-texture-region.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/texture_region")

#### texture\_region Type

`number[]`

#### texture\_region Constraints

**maximum number of items**: the maximum number of items for this array is: `4`

**minimum number of items**: the minimum number of items for this array is: `4`

### type

Discriminator. Optional; absence means `polygon`.

`type`

* is optional

* Type: `string` ([Type](proscenio-defs-polygonsprite-properties-type.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-polygonsprite-properties-type.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/type")

#### type Type

`string` ([Type](proscenio-defs-polygonsprite-properties-type.md))

#### type Constraints

**constant**: the value of this property must be equal to:

```json
"polygon"
```

#### type Default Value

The default value is:

```json
"polygon"
```

### uv



`uv`

* is required

* Type: `number[][]`

* cannot be null

* defined in: [Proscenio character](proscenio-defs-polygonsprite-properties-uv.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/uv")

#### uv Type

`number[][]`

### weights



`weights`

* is optional

* Type: merged type ([Weights](proscenio-defs-polygonsprite-properties-weights.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-polygonsprite-properties-weights.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/PolygonSprite/properties/weights")

#### weights Type

merged type ([Weights](proscenio-defs-polygonsprite-properties-weights.md))

any of

* [Untitled array in Proscenio character](proscenio-defs-polygonsprite-properties-weights-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-polygonsprite-properties-weights-anyof-1.md "check type definition")

## Definitions group Skeleton

Reference this group by using

```json
{"$ref":"https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Skeleton"}
```

| Property        | Type    | Required | Nullable       | Defined by                                                                                                                                                                           |
| :-------------- | :------ | :------- | :------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [bones](#bones) | `array` | Required | cannot be null | [Proscenio character](proscenio-defs-skeleton-properties-bones.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Skeleton/properties/bones") |

### bones



`bones`

* is required

* Type: `object[]` ([Bone](proscenio-defs-bone.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-skeleton-properties-bones.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Skeleton/properties/bones")

#### bones Type

`object[]` ([Bone](proscenio-defs-bone.md))

## Definitions group Slot

Reference this group by using

```json
{"$ref":"https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Slot"}
```

| Property                    | Type     | Required | Nullable       | Defined by                                                                                                                                                                               |
| :-------------------------- | :------- | :------- | :------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [attachments](#attachments) | `array`  | Required | cannot be null | [Proscenio character](proscenio-defs-slot-properties-attachments.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Slot/properties/attachments") |
| [bone](#bone-1)             | Merged   | Optional | cannot be null | [Proscenio character](proscenio-defs-slot-properties-bone.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Slot/properties/bone")               |
| [default](#default)         | Merged   | Optional | cannot be null | [Proscenio character](proscenio-defs-slot-properties-default.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Slot/properties/default")         |
| [name](#name-4)             | `string` | Required | cannot be null | [Proscenio character](proscenio-defs-slot-properties-name.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Slot/properties/name")               |

### attachments



`attachments`

* is required

* Type: `string[]`

* cannot be null

* defined in: [Proscenio character](proscenio-defs-slot-properties-attachments.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Slot/properties/attachments")

#### attachments Type

`string[]`

### bone



`bone`

* is optional

* Type: merged type ([Bone](proscenio-defs-slot-properties-bone.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-slot-properties-bone.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Slot/properties/bone")

#### bone Type

merged type ([Bone](proscenio-defs-slot-properties-bone.md))

any of

* [Untitled string in Proscenio character](proscenio-defs-slot-properties-bone-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-slot-properties-bone-anyof-1.md "check type definition")

### default



`default`

* is optional

* Type: merged type ([Default](proscenio-defs-slot-properties-default.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-slot-properties-default.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Slot/properties/default")

#### default Type

merged type ([Default](proscenio-defs-slot-properties-default.md))

any of

* [Untitled string in Proscenio character](proscenio-defs-slot-properties-default-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-slot-properties-default-anyof-1.md "check type definition")

### name



`name`

* is required

* Type: `string` ([Name](proscenio-defs-slot-properties-name.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-slot-properties-name.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Slot/properties/name")

#### name Type

`string` ([Name](proscenio-defs-slot-properties-name.md))

#### name Constraints

**minimum length**: the minimum number of characters for this string is: `1`

## Definitions group SpriteFrameSprite

Reference this group by using

```json
{"$ref":"https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite"}
```

| Property                             | Type      | Required | Nullable       | Defined by                                                                                                                                                                                                               |
| :----------------------------------- | :-------- | :------- | :------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [bone](#bone-2)                      | `string`  | Required | cannot be null | [Proscenio character](proscenio-defs-spriteframesprite-properties-bone.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/bone")                     |
| [centered](#centered)                | `boolean` | Optional | cannot be null | [Proscenio character](proscenio-defs-spriteframesprite-properties-centered.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/centered")             |
| [frame](#frame-1)                    | `integer` | Optional | cannot be null | [Proscenio character](proscenio-defs-spriteframesprite-properties-frame.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/frame")                   |
| [hframes](#hframes)                  | `integer` | Required | cannot be null | [Proscenio character](proscenio-defs-spriteframesprite-properties-hframes.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/hframes")               |
| [name](#name-5)                      | `string`  | Required | cannot be null | [Proscenio character](proscenio-defs-spriteframesprite-properties-name.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/name")                     |
| [offset](#offset)                    | `array`   | Optional | cannot be null | [Proscenio character](proscenio-defs-spriteframesprite-properties-offset.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/offset")                 |
| [texture](#texture-1)                | Merged    | Optional | cannot be null | [Proscenio character](proscenio-defs-spriteframesprite-properties-texture.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/texture")               |
| [texture\_region](#texture_region-1) | Merged    | Optional | cannot be null | [Proscenio character](proscenio-defs-spriteframesprite-properties-texture-region.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/texture_region") |
| [type](#type-1)                      | `string`  | Required | cannot be null | [Proscenio character](proscenio-defs-spriteframesprite-properties-type.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/type")                     |
| [vframes](#vframes)                  | `integer` | Required | cannot be null | [Proscenio character](proscenio-defs-spriteframesprite-properties-vframes.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/vframes")               |

### bone



`bone`

* is required

* Type: `string` ([Bone](proscenio-defs-spriteframesprite-properties-bone.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-spriteframesprite-properties-bone.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/bone")

#### bone Type

`string` ([Bone](proscenio-defs-spriteframesprite-properties-bone.md))

### centered



`centered`

* is optional

* Type: `boolean` ([Centered](proscenio-defs-spriteframesprite-properties-centered.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-spriteframesprite-properties-centered.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/centered")

#### centered Type

`boolean` ([Centered](proscenio-defs-spriteframesprite-properties-centered.md))

#### centered Default Value

The default value is:

```json
true
```

### frame

Initial frame index (row-major). Animation tracks override at runtime.

`frame`

* is optional

* Type: `integer` ([Frame](proscenio-defs-spriteframesprite-properties-frame.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-spriteframesprite-properties-frame.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/frame")

#### frame Type

`integer` ([Frame](proscenio-defs-spriteframesprite-properties-frame.md))

#### frame Constraints

**minimum**: the value of this number must greater than or equal to: `0`

### hframes



`hframes`

* is required

* Type: `integer` ([Hframes](proscenio-defs-spriteframesprite-properties-hframes.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-spriteframesprite-properties-hframes.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/hframes")

#### hframes Type

`integer` ([Hframes](proscenio-defs-spriteframesprite-properties-hframes.md))

#### hframes Constraints

**minimum**: the value of this number must greater than or equal to: `1`

### name



`name`

* is required

* Type: `string` ([Name](proscenio-defs-spriteframesprite-properties-name.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-spriteframesprite-properties-name.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/name")

#### name Type

`string` ([Name](proscenio-defs-spriteframesprite-properties-name.md))

#### name Constraints

**minimum length**: the minimum number of characters for this string is: `1`

### offset



`offset`

* is optional

* Type: `number[]`

* cannot be null

* defined in: [Proscenio character](proscenio-defs-spriteframesprite-properties-offset.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/offset")

#### offset Type

`number[]`

#### offset Constraints

**maximum number of items**: the maximum number of items for this array is: `2`

**minimum number of items**: the minimum number of items for this array is: `2`

#### offset Default Value

The default value is:

```json
[
  0,
  0
]
```

### texture

Optional per-sprite texture filename, resolved relative to the .proscenio document. Mirrors the polygon-sprite field. Importers fall back to the top-level `atlas` field when absent.

`texture`

* is optional

* Type: merged type ([Texture](proscenio-defs-spriteframesprite-properties-texture.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-spriteframesprite-properties-texture.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/texture")

#### texture Type

merged type ([Texture](proscenio-defs-spriteframesprite-properties-texture.md))

any of

* [Untitled string in Proscenio character](proscenio-defs-spriteframesprite-properties-texture-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-spriteframesprite-properties-texture-anyof-1.md "check type definition")

### texture\_region

Optional sub-rectangle within the atlas where the spritesheet lives. Absent means use the full atlas.

`texture_region`

* is optional

* Type: merged type ([Texture Region](proscenio-defs-spriteframesprite-properties-texture-region.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-spriteframesprite-properties-texture-region.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/texture_region")

#### texture\_region Type

merged type ([Texture Region](proscenio-defs-spriteframesprite-properties-texture-region.md))

any of

* [Untitled array in Proscenio character](proscenio-defs-spriteframesprite-properties-texture-region-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-spriteframesprite-properties-texture-region-anyof-1.md "check type definition")

### type

Discriminator. Required and constant.

`type`

* is required

* Type: `string` ([Type](proscenio-defs-spriteframesprite-properties-type.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-spriteframesprite-properties-type.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/type")

#### type Type

`string` ([Type](proscenio-defs-spriteframesprite-properties-type.md))

#### type Constraints

**constant**: the value of this property must be equal to:

```json
"sprite_frame"
```

### vframes



`vframes`

* is required

* Type: `integer` ([Vframes](proscenio-defs-spriteframesprite-properties-vframes.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-spriteframesprite-properties-vframes.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/vframes")

#### vframes Type

`integer` ([Vframes](proscenio-defs-spriteframesprite-properties-vframes.md))

#### vframes Constraints

**minimum**: the value of this number must greater than or equal to: `1`

## Definitions group Track

Reference this group by using

```json
{"$ref":"https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Track"}
```

| Property          | Type     | Required | Nullable       | Defined by                                                                                                                                                                       |
| :---------------- | :------- | :------- | :------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [keys](#keys)     | `array`  | Required | cannot be null | [Proscenio character](proscenio-defs-track-properties-keys.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Track/properties/keys")     |
| [target](#target) | `string` | Required | cannot be null | [Proscenio character](proscenio-defs-track-properties-target.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Track/properties/target") |
| [type](#type-2)   | `string` | Required | cannot be null | [Proscenio character](proscenio-defs-track-properties-type.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Track/properties/type")     |

### keys



`keys`

* is required

* Type: `object[]` ([Key](proscenio-defs-key.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-track-properties-keys.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Track/properties/keys")

#### keys Type

`object[]` ([Key](proscenio-defs-key.md))

### target



`target`

* is required

* Type: `string` ([Target](proscenio-defs-track-properties-target.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-track-properties-target.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Track/properties/target")

#### target Type

`string` ([Target](proscenio-defs-track-properties-target.md))

#### target Constraints

**minimum length**: the minimum number of characters for this string is: `1`

### type



`type`

* is required

* Type: `string` ([Type](proscenio-defs-track-properties-type.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-track-properties-type.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Track/properties/type")

#### type Type

`string` ([Type](proscenio-defs-track-properties-type.md))

#### type Constraints

**enum**: the value of this property must be equal to one of the following values:

| Value               | Explanation |
| :------------------ | :---------- |
| `"bone_transform"`  |             |
| `"sprite_frame"`    |             |
| `"slot_attachment"` |             |
| `"visibility"`      |             |

## Definitions group Weight

Reference this group by using

```json
{"$ref":"https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Weight"}
```

| Property          | Type     | Required | Nullable       | Defined by                                                                                                                                                                         |
| :---------------- | :------- | :------- | :------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [bone](#bone-3)   | `string` | Required | cannot be null | [Proscenio character](proscenio-defs-weight-properties-bone.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Weight/properties/bone")     |
| [values](#values) | `array`  | Required | cannot be null | [Proscenio character](proscenio-defs-weight-properties-values.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Weight/properties/values") |

### bone



`bone`

* is required

* Type: `string` ([Bone](proscenio-defs-weight-properties-bone.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-weight-properties-bone.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Weight/properties/bone")

#### bone Type

`string` ([Bone](proscenio-defs-weight-properties-bone.md))

### values



`values`

* is required

* Type: `number[]`

* cannot be null

* defined in: [Proscenio character](proscenio-defs-weight-properties-values.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Weight/properties/values")

#### values Type

`number[]`
