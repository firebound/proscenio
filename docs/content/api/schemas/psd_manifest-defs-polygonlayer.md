# PolygonLayer Schema

```txt
https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/properties/layers/items/oneOf/0
```

Single PNG, single quad mesh.

`kind: "mesh"` is a polygon superset flagged as a deformable mesh
source; renders as polygon when no rig is bound.

| Abstract            | Extensible | Status         | Identifiable | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                                     |
| :------------------ | :--------- | :------------- | :----------- | :---------------- | :-------------------- | :------------------ | :--------------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | No           | Forbidden         | Forbidden             | none                | [psd\_manifest.schema.json\*](../../../../out/psd_manifest.schema.json "open original schema") |

## 0 Type

`object` ([PolygonLayer](psd_manifest-defs-polygonlayer.md))

## 0 Properties

| Property                   | Type      | Required | Nullable       | Defined by                                                                                                                                                                                                      |
| :------------------------- | :-------- | :------- | :------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [blend\_mode](#blend_mode) | Merged    | Optional | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-blend-mode.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/blend_mode") |
| [kind](#kind)              | `string`  | Required | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-kind.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/kind")             |
| [name](#name)              | `string`  | Required | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-name.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/name")             |
| [origin](#origin)          | Merged    | Optional | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-origin.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/origin")         |
| [path](#path)              | `string`  | Required | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-path.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/path")             |
| [position](#position)      | `array`   | Required | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-position.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/position")     |
| [size](#size)              | `array`   | Required | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-size.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/size")             |
| [subfolder](#subfolder)    | Merged    | Optional | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-subfolder.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/subfolder")   |
| [z\_order](#z_order)       | `integer` | Required | cannot be null | [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-z-order.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/z_order")       |

## blend\_mode

Layer blend mode emitted from the PSD; importer maps to material blend mode.

`blend_mode`

* is optional

* Type: merged type ([Blend Mode](psd_manifest-defs-polygonlayer-properties-blend-mode.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-blend-mode.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/blend_mode")

### blend\_mode Type

merged type ([Blend Mode](psd_manifest-defs-polygonlayer-properties-blend-mode.md))

any of

* [Untitled string in Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-blend-mode-anyof-0.md "check type definition")

* [Untitled null in Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-blend-mode-anyof-1.md "check type definition")

## kind

`kind`

* is required

* Type: `string` ([Kind](psd_manifest-defs-polygonlayer-properties-kind.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-kind.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/kind")

### kind Type

`string` ([Kind](psd_manifest-defs-polygonlayer-properties-kind.md))

### kind Constraints

**enum**: the value of this property must be equal to one of the following values:

| Value       | Explanation |
| :---------- | :---------- |
| `"polygon"` |             |
| `"mesh"`    |             |

## name

`name`

* is required

* Type: `string` ([Name](psd_manifest-defs-polygonlayer-properties-name.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-name.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/name")

### name Type

`string` ([Name](psd_manifest-defs-polygonlayer-properties-name.md))

### name Constraints

**minimum length**: the minimum number of characters for this string is: `1`

## origin

Optional pivot in PSD pixels. Set by the \[origin:x,y] tag or by an \[origin] marker layer inside the group. Importer uses this as the mesh's Object.location when present; falls back to bbox center otherwise.

`origin`

* is optional

* Type: merged type ([Origin](psd_manifest-defs-polygonlayer-properties-origin.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-origin.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/origin")

### origin Type

merged type ([Origin](psd_manifest-defs-polygonlayer-properties-origin.md))

any of

* [Untitled array in Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-origin-anyof-0.md "check type definition")

* [Untitled null in Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-origin-anyof-1.md "check type definition")

## path

Path to the layer PNG, relative to the manifest file.

`path`

* is required

* Type: `string` ([Path](psd_manifest-defs-polygonlayer-properties-path.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-path.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/path")

### path Type

`string` ([Path](psd_manifest-defs-polygonlayer-properties-path.md))

### path Constraints

**minimum length**: the minimum number of characters for this string is: `1`

## position

PSD top-left bbox of the layer in pixels.

`position`

* is required

* Type: `integer[]`

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-position.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/position")

### position Type

`integer[]`

### position Constraints

**maximum number of items**: the maximum number of items for this array is: `2`

**minimum number of items**: the minimum number of items for this array is: `2`

## size

Layer bbox size in pixels.

`size`

* is required

* Type: `integer[]`

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-size.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/size")

### size Type

`integer[]`

### size Constraints

**maximum number of items**: the maximum number of items for this array is: `2`

**minimum number of items**: the minimum number of items for this array is: `2`

## subfolder

Optional output sub-folder under images/, set by the \[folder:name] tag. Importer ignores; this is purely a disk-layout hint reflected in `path`.

`subfolder`

* is optional

* Type: merged type ([Subfolder](psd_manifest-defs-polygonlayer-properties-subfolder.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-subfolder.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/subfolder")

### subfolder Type

merged type ([Subfolder](psd_manifest-defs-polygonlayer-properties-subfolder.md))

any of

* [Untitled string in Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-subfolder-anyof-0.md "check type definition")

* [Untitled null in Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-subfolder-anyof-1.md "check type definition")

## z\_order

Stack index, 0 = top.

`z_order`

* is required

* Type: `integer` ([Z Order](psd_manifest-defs-polygonlayer-properties-z-order.md))

* cannot be null

* defined in: [Proscenio PSD manifest](psd_manifest-defs-polygonlayer-properties-z-order.md "https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/$defs/PolygonLayer/properties/z_order")

### z\_order Type

`integer` ([Z Order](psd_manifest-defs-polygonlayer-properties-z-order.md))

### z\_order Constraints

**minimum**: the value of this number must greater than or equal to: `0`
