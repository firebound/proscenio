# Track Schema

```txt
https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Track
```

| Abstract            | Extensible | Status         | Identifiable | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                              |
| :------------------ | :--------- | :------------- | :----------- | :---------------- | :-------------------- | :------------------ | :-------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | No           | Forbidden         | Forbidden             | none                | [proscenio.schema.json\*](../../../../out/proscenio.schema.json "open original schema") |

## Track Type

`object` ([Track](proscenio-defs-track.md))

## Track Properties

| Property          | Type     | Required | Nullable       | Defined by                                                                                                                                                                       |
| :---------------- | :------- | :------- | :------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [keys](#keys)     | `array`  | Required | cannot be null | [Proscenio character](proscenio-defs-track-properties-keys.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Track/properties/keys")     |
| [target](#target) | `string` | Required | cannot be null | [Proscenio character](proscenio-defs-track-properties-target.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Track/properties/target") |
| [type](#type)     | `string` | Required | cannot be null | [Proscenio character](proscenio-defs-track-properties-type.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Track/properties/type")     |

## keys

`keys`

* is required

* Type: `object[]` ([Key](proscenio-defs-key.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-track-properties-keys.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Track/properties/keys")

### keys Type

`object[]` ([Key](proscenio-defs-key.md))

## target

`target`

* is required

* Type: `string` ([Target](proscenio-defs-track-properties-target.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-track-properties-target.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Track/properties/target")

### target Type

`string` ([Target](proscenio-defs-track-properties-target.md))

### target Constraints

**minimum length**: the minimum number of characters for this string is: `1`

## type

`type`

* is required

* Type: `string` ([Type](proscenio-defs-track-properties-type.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-track-properties-type.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Track/properties/type")

### type Type

`string` ([Type](proscenio-defs-track-properties-type.md))

### type Constraints

**enum**: the value of this property must be equal to one of the following values:

| Value               | Explanation |
| :------------------ | :---------- |
| `"bone_transform"`  |             |
| `"sprite_frame"`    |             |
| `"slot_attachment"` |             |
| `"visibility"`      |             |
