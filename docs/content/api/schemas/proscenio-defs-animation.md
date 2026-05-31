# Animation Schema

```txt
https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/properties/animations/anyOf/0/items
```



| Abstract            | Extensible | Status         | Identifiable | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                              |
| :------------------ | :--------- | :------------- | :----------- | :---------------- | :-------------------- | :------------------ | :-------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | No           | Forbidden         | Forbidden             | none                | [proscenio.schema.json\*](../../../../out/proscenio.schema.json "open original schema") |

## items Type

`object` ([Animation](proscenio-defs-animation.md))

# items Properties

| Property          | Type     | Required | Nullable       | Defined by                                                                                                                                                                               |
| :---------------- | :------- | :------- | :------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [length](#length) | `number` | Required | cannot be null | [Proscenio character](proscenio-defs-animation-properties-length.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Animation/properties/length") |
| [loop](#loop)     | Merged   | Optional | cannot be null | [Proscenio character](proscenio-defs-animation-properties-loop.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Animation/properties/loop")     |
| [name](#name)     | `string` | Required | cannot be null | [Proscenio character](proscenio-defs-animation-properties-name.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Animation/properties/name")     |
| [tracks](#tracks) | `array`  | Required | cannot be null | [Proscenio character](proscenio-defs-animation-properties-tracks.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Animation/properties/tracks") |

## length



`length`

* is required

* Type: `number` ([Length](proscenio-defs-animation-properties-length.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-animation-properties-length.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Animation/properties/length")

### length Type

`number` ([Length](proscenio-defs-animation-properties-length.md))

### length Constraints

**minimum (exclusive)**: the value of this number must be greater than: `0`

## loop



`loop`

* is optional

* Type: merged type ([Loop](proscenio-defs-animation-properties-loop.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-animation-properties-loop.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Animation/properties/loop")

### loop Type

merged type ([Loop](proscenio-defs-animation-properties-loop.md))

any of

* [Untitled boolean in Proscenio character](proscenio-defs-animation-properties-loop-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-animation-properties-loop-anyof-1.md "check type definition")

## name



`name`

* is required

* Type: `string` ([Name](proscenio-defs-animation-properties-name.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-animation-properties-name.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Animation/properties/name")

### name Type

`string` ([Name](proscenio-defs-animation-properties-name.md))

### name Constraints

**minimum length**: the minimum number of characters for this string is: `1`

## tracks



`tracks`

* is required

* Type: `object[]` ([Track](proscenio-defs-track.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-animation-properties-tracks.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Animation/properties/tracks")

### tracks Type

`object[]` ([Track](proscenio-defs-track.md))
