# Bone Schema

```txt
https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Skeleton/properties/bones/items
```

| Abstract            | Extensible | Status         | Identifiable | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                              |
| :------------------ | :--------- | :------------- | :----------- | :---------------- | :-------------------- | :------------------ | :-------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | No           | Forbidden         | Forbidden             | none                | [proscenio.schema.json\*](../../../../out/proscenio.schema.json "open original schema") |

## items Type

`object` ([Bone](proscenio-defs-bone.md))

## items Properties

| Property              | Type     | Required | Nullable       | Defined by                                                                                                                                                                         |
| :-------------------- | :------- | :------- | :------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [length](#length)     | Merged   | Optional | cannot be null | [Proscenio character](proscenio-defs-bone-properties-length.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Bone/properties/length")     |
| [name](#name)         | `string` | Required | cannot be null | [Proscenio character](proscenio-defs-bone-properties-name.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Bone/properties/name")         |
| [parent](#parent)     | Merged   | Optional | cannot be null | [Proscenio character](proscenio-defs-bone-properties-parent.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Bone/properties/parent")     |
| [position](#position) | Merged   | Optional | cannot be null | [Proscenio character](proscenio-defs-bone-properties-position.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Bone/properties/position") |
| [rotation](#rotation) | Merged   | Optional | cannot be null | [Proscenio character](proscenio-defs-bone-properties-rotation.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Bone/properties/rotation") |
| [scale](#scale)       | Merged   | Optional | cannot be null | [Proscenio character](proscenio-defs-bone-properties-scale.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Bone/properties/scale")       |

## length

`length`

* is optional

* Type: merged type ([Length](proscenio-defs-bone-properties-length.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-bone-properties-length.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Bone/properties/length")

### length Type

merged type ([Length](proscenio-defs-bone-properties-length.md))

any of

* [Untitled number in Proscenio character](proscenio-defs-bone-properties-length-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-bone-properties-length-anyof-1.md "check type definition")

## name

`name`

* is required

* Type: `string` ([Name](proscenio-defs-bone-properties-name.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-bone-properties-name.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Bone/properties/name")

### name Type

`string` ([Name](proscenio-defs-bone-properties-name.md))

### name Constraints

**minimum length**: the minimum number of characters for this string is: `1`

## parent

`parent`

* is optional

* Type: merged type ([Parent](proscenio-defs-bone-properties-parent.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-bone-properties-parent.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Bone/properties/parent")

### parent Type

merged type ([Parent](proscenio-defs-bone-properties-parent.md))

any of

* [Untitled string in Proscenio character](proscenio-defs-bone-properties-parent-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-bone-properties-parent-anyof-1.md "check type definition")

## position

`position`

* is optional

* Type: merged type ([Position](proscenio-defs-bone-properties-position.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-bone-properties-position.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Bone/properties/position")

### position Type

merged type ([Position](proscenio-defs-bone-properties-position.md))

any of

* [Untitled array in Proscenio character](proscenio-defs-bone-properties-position-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-bone-properties-position-anyof-1.md "check type definition")

## rotation

`rotation`

* is optional

* Type: merged type ([Rotation](proscenio-defs-bone-properties-rotation.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-bone-properties-rotation.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Bone/properties/rotation")

### rotation Type

merged type ([Rotation](proscenio-defs-bone-properties-rotation.md))

any of

* [Untitled number in Proscenio character](proscenio-defs-bone-properties-rotation-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-bone-properties-rotation-anyof-1.md "check type definition")

## scale

`scale`

* is optional

* Type: merged type ([Scale](proscenio-defs-bone-properties-scale.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-bone-properties-scale.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Bone/properties/scale")

### scale Type

merged type ([Scale](proscenio-defs-bone-properties-scale.md))

any of

* [Untitled array in Proscenio character](proscenio-defs-bone-properties-scale-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-bone-properties-scale-anyof-1.md "check type definition")
