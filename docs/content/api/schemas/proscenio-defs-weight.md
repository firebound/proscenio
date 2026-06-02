# Weight Schema

```txt
https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Weight
```

| Abstract            | Extensible | Status         | Identifiable | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                              |
| :------------------ | :--------- | :------------- | :----------- | :---------------- | :-------------------- | :------------------ | :-------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | No           | Forbidden         | Forbidden             | none                | [proscenio.schema.json\*](../../../../out/proscenio.schema.json "open original schema") |

## Weight Type

`object` ([Weight](proscenio-defs-weight.md))

## Weight Properties

| Property          | Type     | Required | Nullable       | Defined by                                                                                                                                                                         |
| :---------------- | :------- | :------- | :------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [bone](#bone)     | `string` | Required | cannot be null | [Proscenio character](proscenio-defs-weight-properties-bone.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Weight/properties/bone")     |
| [values](#values) | `array`  | Required | cannot be null | [Proscenio character](proscenio-defs-weight-properties-values.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Weight/properties/values") |

## bone

`bone`

* is required

* Type: `string` ([Bone](proscenio-defs-weight-properties-bone.md))

* cannot be null

* defined in: [Proscenio character](proscenio-defs-weight-properties-bone.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Weight/properties/bone")

### bone Type

`string` ([Bone](proscenio-defs-weight-properties-bone.md))

## values

`values`

* is required

* Type: `number[]`

* cannot be null

* defined in: [Proscenio character](proscenio-defs-weight-properties-values.md "https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/Weight/properties/values")

### values Type

`number[]`
