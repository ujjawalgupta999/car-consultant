# AMULATE SUMMER HACKATHON 2026: A2UI SPECIFICATION
## AI-Powered Car Rental and Purchase Consultant

---

## 1. Overview and Protocol Principles

**A2UI (Agent-to-User Interface)** is an open, declarative protocol for generative UI that allows conversational AI agents to stream and render rich native interfaces directly inside conversational threads without executing arbitrary code.

### Core Tenets:
1. **Declarative Flat Structure**: Component trees are expressed as flat adjacency lists with explicit `id` references, optimized for LLM streaming and low cognitive fragility.
2. **Data-Model Separation**: Visual layouts (`updateComponents`) are decoupled from state values (`updateDataModel`).
3. **Strict Whitelist**: Host clients only instantiate approved native components from a pre-defined catalog.
4. **Bidirectional RPC**: User interactions trigger structured `actionResponse` events dispatched back to the agent backend.

---

## 2. Protocol Messages

### 2.1 Server-to-Client Messages

#### 1. `createSurface`
Signals the client to mount a new UI surface.
```json
{
  "type": "createSurface",
  "surfaceId": "surf_interview_step1",
  "catalogId": "automotive-standard-v1",
  "title": "Vehicle Preferences",
  "position": "inline"
}
```

#### 2. `updateComponents`
Supplies or updates a flat array of component blueprints.
```json
{
  "type": "updateComponents",
  "surfaceId": "surf_interview_step1",
  "components": [
    {
      "id": "root_card",
      "component": "Card",
      "properties": {
        "variant": "glass",
        "padding": "md"
      },
      "children": ["intent_selector", "category_grid", "submit_btn"]
    },
    {
      "id": "intent_selector",
      "component": "RadioGroup",
      "properties": {
        "label": "Choose Intent",
        "dataBinding": "userPreferences.intent",
        "options": [
          { "label": "🚗 Rent a Vehicle", "value": "rent" },
          { "label": "🏷️ Buy a Vehicle", "value": "buy" }
        ]
      }
    },
    {
      "id": "category_grid",
      "component": "Grid",
      "properties": { "columns": 2, "gap": "sm" },
      "children": ["cat_suv", "cat_sedan", "cat_ev"]
    },
    {
      "id": "cat_suv",
      "component": "Button",
      "properties": {
        "variant": "outline",
        "text": "SUV",
        "actionId": "select_category",
        "actionData": { "category": "SUV" }
      }
    },
    {
      "id": "submit_btn",
      "component": "Button",
      "properties": {
        "variant": "primary",
        "text": "Find My Cars",
        "actionId": "start_search"
      }
    }
  ]
}
```

#### 3. `updateDataModel`
Pushes data updates into the surface's reactive state store.
```json
{
  "type": "updateDataModel",
  "surfaceId": "surf_interview_step1",
  "path": "userPreferences.intent",
  "value": "rent"
}
```

#### 4. `deleteSurface`
Tear down a surface when replaced or completed.
```json
{
  "type": "deleteSurface",
  "surfaceId": "surf_interview_step1"
}
```

### 2.2 Client-to-Server Messages (`actionResponse`)
Dispatched when a user interacts with an A2UI widget:
```json
{
  "type": "actionResponse",
  "surfaceId": "surf_interview_step1",
  "actionId": "select_category",
  "data": {
    "category": "SUV"
  },
  "timestamp": "2026-11-04T16:15:10Z"
}
```

---

## 3. Approved Component Catalog (`automotive-standard-v1`)

| Component | Category | Supported Properties |
|-----------|----------|----------------------|
| `Container` | Layout | `padding`, `direction` (row/column), `gap`, `background` |
| `Card` | Layout | `variant` (glass, elevated, flat, bordered), `header`, `footer` |
| `Grid` | Layout | `columns` (1-4), `gap`, `responsive` |
| `Text` | Display | `content`, `size` (xs-2xl), `weight`, `color`, `markdown` (safe) |
| `Badge` | Display | `text`, `variant` (success, warning, cyan, muted) |
| `VehicleCard` | Automotive | `vehicle`, `matchScore`, `breakdown`, `onSelectAction` |
| `ProgressTimeline` | Agent | `steps`, `currentStep`, `completedSteps` |
| `Button` | Input | `text`, `variant` (primary, secondary, outline, danger), `actionId`, `actionData`, `disabled` |
| `TextInput` | Input | `label`, `placeholder`, `dataBinding`, `type` (text, number, date) |
| `RadioGroup` | Input | `label`, `options`, `dataBinding`, `actionId` |
| `Slider` | Input | `label`, `min`, `max`, `step`, `unit`, `dataBinding` |

---

## 4. Security & Sanitization

1. **No Code Execution**:
   - The React renderer maps the `component` string to a static dictionary of React components (`ComponentRegistry`).
   - Unknown component names fall back to a safe text representation or warning badge.
2. **Data Sanitization**:
   - Text interpolation using DOMPurify or safe React JSX text children. No `dangerouslySetInnerHTML`.
3. **Action Validation**:
   - Every `actionId` received by the backend is validated against allowable state transitions in the workflow state machine.

