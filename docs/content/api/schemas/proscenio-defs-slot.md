# Slot Schema

```txt
https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/properties/slots/anyOf/0/items
```

| Abstract            | Extensible | Status         | Identifiable | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                              |
| :------------------ | :--------- | :------------- | :----------- | :---------------- | :-------------------- | :------------------ | :-------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | No           | Forbidden         | Forbidden             | none                | [proscenio.schema.json\*](../../../../out/proscenio.schema.json "open original schema") |

## items Type

`object` ([Slot](proscenio-defs-slot.md))

## items Properties

| Property                    | Type     | Required | Nullable       | Defined by                                                                                                                                                                               |
| :-------------------------- | :------- | :------- | :------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [attachments](#attachments) | `array`  | Required | cannot be null | [Proscenio character](proscenio-defs-slot-properties-attachments.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Slot/properties/attachments") |
| [bone](#bone)               | Merged   | Optional | cannot be null | [Proscenio character](proscenio-defs-slot-properties-bone.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Slot/properties/bone")               |
| [default](#default)         | Merged   | Optional | cannot be null | [Proscenio character](proscenio-defs-slot-properties-default.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Slot/properties/default")         |
| [name](#name)               | `string` | Required | cannot be null | [Proscenio character](proscenio-defs-slot-properties-name.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Slot/properties/name")               |

## attachments

`attachments`

* is required

* Type: `string[]`

* cannot be null

* defined in: [Proscenio character](proscenio-defs-slot-properties-attachments.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Slot/properties/attachments")

### attachments Type

`string[]`

## bone

`bone`

* is optional

* Type: merged type ([Bone](proscenio-defs-slot-properties-bone.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-slot-properties-bone.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Slot/properties/bone")

### bone Type

merged type ([Bone](proscenio-defs-slot-properties-bone.md))

any of

* [Untitled string in Proscenio character](proscenio-defs-slot-properties-bone-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-slot-properties-bone-anyof-1.md "check type definition")

## default

`default`

* is optional

* Type: merged type ([Default](proscenio-defs-slot-properties-default.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-slot-properties-default.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Slot/properties/default")

### default Type

merged type ([Default](proscenio-defs-slot-properties-default.md))

any of

* [Untitled string in Proscenio character](proscenio-defs-slot-properties-default-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-slot-properties-default-anyof-1.md "check type definition")

## name

`name`

* is required

* Type: `string` ([Name](proscenio-defs-slot-properties-name.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-slot-properties-name.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Slot/properties/name")

### name Type

`string` ([Name](proscenio-defs-slot-properties-name.md))

### name Constraints

**minimum length**: the minimum number of characters for this string is: `1`
