# FrameEntry Schema

```txt
https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/SpriteFrameLayer/properties/frames/items
```

| Abstract            | Extensible | Status         | Identifiable | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                                     |
| :------------------ | :--------- | :------------- | :----------- | :---------------- | :-------------------- | :------------------ | :--------------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | No           | Forbidden         | Forbidden             | none                | [psd\_manifest.schema.json\*](../../../../out/psd_manifest.schema.json "open original schema") |

## items Type

`object` ([FrameEntry](psd_manifest-defs-frameentry.md))

## items Properties

| Property        | Type      | Required | Nullable       | Defined by                                                                                                                                                                                        |
| :-------------- | :-------- | :------- | :------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [index](#index) | `integer` | Required | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-frameentry-properties-index.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/FrameEntry/properties/index") |
| [path](#path)   | `string`  | Required | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-frameentry-properties-path.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/FrameEntry/properties/path")   |

## index

Frame index, 0-based, contiguous, ordered.

`index`

* is required

* Type: `integer` ([Index](psd_manifest-defs-frameentry-properties-index.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-frameentry-properties-index.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/FrameEntry/properties/index")

### index Type

`integer` ([Index](psd_manifest-defs-frameentry-properties-index.md))

### index Constraints

**minimum**: the value of this number must greater than or equal to: `0`

## path

Path to the frame PNG, relative to the manifest file.

`path`

* is required

* Type: `string` ([Path](psd_manifest-defs-frameentry-properties-path.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-frameentry-properties-path.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/FrameEntry/properties/path")

### path Type

`string` ([Path](psd_manifest-defs-frameentry-properties-path.md))

### path Constraints

**minimum length**: the minimum number of characters for this string is: `1`
