---
name: Gridbot live view
description: A dark robotics data viewer that draws what a simulated warehouse robot senses, believes and plans.
colors:
  canvas: "#0d0f13"
  panel: "#0f1217"
  chrome: "#12151b"
  raised: "#1a1e26"
  row-selected: "#161b23"
  segment-selected: "#263246"
  rule: "#222730"
  edge: "#2a303b"
  edge-strong: "#3a414d"
  ink: "#e6eaf0"
  text: "#c9d1dc"
  text-secondary: "#a3acb9"
  muted-control: "#8d96a5"
  muted: "#7d8796"
  faint: "#6c7686"
  floor: "#18202a"
  grid: "rgba(255,255,255,0.055)"
  wall-cell: "rgb(214,222,233)"
  driven-path: "rgba(255,255,255,0.28)"
  scan-amber: "#ffd166"
  plan-blue: "#5aa9ff"
  queued-edge: "#24405f"
  odom-pink: "#ff6b9a"
  axis-red: "#ff5c5c"
  ok-green: "#3ddc84"
  live-ink: "#9be3b5"
  live-edge: "#263b2e"
  done-edge: "#24493a"
  done-fill: "#1d2a22"
typography:
  title:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', sans-serif"
    fontSize: "15px"
    fontWeight: 600
  heading:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', sans-serif"
    fontSize: "12px"
    fontWeight: 600
    letterSpacing: "0.02em"
  body:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.35
  label:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', sans-serif"
    fontSize: "12px"
    fontWeight: 400
  chip:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', sans-serif"
    fontSize: "11px"
    fontWeight: 600
  value:
    fontFamily: "'JetBrains Mono', monospace"
    fontSize: "13px"
    fontWeight: 400
    fontFeature: "tnum"
  topic:
    fontFamily: "'JetBrains Mono', monospace"
    fontSize: "11px"
    fontWeight: 400
  map-label:
    fontFamily: "'JetBrains Mono', monospace"
    fontSize: "11px"
    fontWeight: 500
rounded:
  bar: "3px"
  control: "4px"
  button: "5px"
  card: "6px"
  pill: "99px"
spacing:
  hairline: "1px"
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "14px"
components:
  button-secondary:
    backgroundColor: "{colors.raised}"
    textColor: "{colors.ink}"
    rounded: "{rounded.button}"
    padding: "0 12px"
    height: "30px"
  segment:
    backgroundColor: "transparent"
    textColor: "{colors.muted-control}"
    rounded: "{rounded.control}"
    padding: "0 10px"
    height: "26px"
  segment-selected:
    backgroundColor: "{colors.segment-selected}"
    textColor: "{colors.ink}"
  tab:
    backgroundColor: "transparent"
    textColor: "{colors.muted}"
    typography: "{typography.heading}"
    padding: "0 12px"
    height: "38px"
  tab-selected:
    textColor: "{colors.ink}"
  layer-row:
    backgroundColor: "transparent"
    textColor: "{colors.text}"
    typography: "{typography.body}"
    padding: "6px 12px"
  layer-chip:
    backgroundColor: "{colors.chrome}"
    textColor: "{colors.text}"
    rounded: "{rounded.button}"
    padding: "0 9px"
    height: "34px"
  status-pill-live:
    textColor: "{colors.live-ink}"
    rounded: "{rounded.pill}"
    padding: "3px 9px"
  status-pill-paused:
    textColor: "{colors.text-secondary}"
    rounded: "{rounded.pill}"
    padding: "3px 9px"
  chip-locked:
    textColor: "{colors.faint}"
    rounded: "{rounded.pill}"
    typography: "{typography.chip}"
    padding: "2px 7px"
  chip-queued:
    textColor: "{colors.plan-blue}"
    rounded: "{rounded.pill}"
    typography: "{typography.chip}"
    padding: "2px 7px"
  chip-active:
    backgroundColor: "{colors.plan-blue}"
    textColor: "{colors.canvas}"
    rounded: "{rounded.pill}"
    typography: "{typography.chip}"
    padding: "2px 7px"
  chip-done:
    textColor: "{colors.ok-green}"
    rounded: "{rounded.pill}"
    typography: "{typography.chip}"
    padding: "2px 7px"
  card:
    backgroundColor: "{colors.chrome}"
    rounded: "{rounded.card}"
    padding: "10px 12px"
  objective-row:
    backgroundColor: "transparent"
    textColor: "{colors.text}"
    typography: "{typography.body}"
    padding: "7px 12px 7px 10px"
  objective-row-selected:
    backgroundColor: "{colors.row-selected}"
---

# Design System: Gridbot live view

## Overview

**Creative North Star: "The Robot's Debug Console"**

The live view looks like the tool a robotics team would keep open while their robot runs. It follows the Foxglove style of data viewer, finished to the level of Linear or Vercel. Near-black panels sit edge to edge, divided by 1px rules. The map gets most of the screen and every panel around it reads real algorithm state. The look comes from the data colours on a dark field. There is no illustration, no mascot and no decorative chrome.

Density is high but calm. Body text is 13px, headings are 12px semibold, and every number is set in JetBrains Mono with tabular figures, so values hold still while they change at 20 Hz. Colour belongs to the data. The panels stay grey, and amber, blue, pink, red and green appear only where they encode something the robot produced or a control the visitor uses.

The source of truth today is the prototype at `Console.dc.html`, generated by the scratchpad console scripts. It stays the reference until `ui/src` implements the view in TypeScript. Visitors change only their own view (camera, tab, layers, selection, pause). Nothing on screen lets them change the simulation. The North Star name was derived from PRODUCT.md and has not been confirmed by the owner.

**Key Characteristics:**

- Edge-to-edge dark panels split by 1px hairlines, with no shadows.
- One map in the centre, a layer list on the left and a tabbed inspector on the right.
- Data colours on grey chrome, with each data colour tied to a ROS topic.
- Mono tabular numbers for every value, system UI for everything else.
- Blank space where the robot has not looked yet.

## Colors

Grey-blue near-blacks carry the chrome, and five saturated data colours carry the robot's state.

### Primary

- **Plan Blue** (plan-blue): the planned path, objective markers, the selected tab underline, the selected objective number, active status chips, progress fill, slider accents, the Reset link and the focus ring. It is the colour of intent and of anything the visitor can operate.

### Secondary

- **Scan Amber** (scan-amber): lidar returns, the sweep head on the map and in the polar plot, and the scan swatch. It is used for nothing else.
- **Odometry Pink** (odom-pink): the dashed odometry estimate footprint, the error plot line, the Estimate column header and the "Estimate off" value. Pink always means the robot's belief where it differs from the truth.

### Tertiary

- **Signal Green** (ok-green): the TF y axis on the robot, done states (stepper bar, run segments, done chips and done markers) and the live dot in the status pill. Its tints `live-ink`, `live-edge`, `done-edge` and `done-fill` belong to those same states.
- **Axis Red** (axis-red): the TF x axis on the robot, on the map and in Robot POV.

### Neutral

- **Canvas** (canvas): the map stage, the root background and the dark fill inside queued objective markers.
- **Panel** (panel): the layer column and the inspector column.
- **Chrome** (chrome): the toolbar, footer, cards and phone layer chips.
- **Raised** (raised): the pause button and checkbox fill.
- **Rule** (rule): every 1px divider, track backgrounds for progress bars and run segments, and error plot rules.
- **Edge** (edge) and **Edge Strong** (edge-strong): control outlines. Edge outlines the camera group, the floating camera card, phone chips, the locked chip and the paused pill; Edge Strong outlines the pause button and checkboxes.
- **Ink** (ink): headings, values and the true robot outline.
- **Text** (text), **Text Secondary** (text-secondary), **Muted** (muted) and **Faint** (faint): body copy, secondary values and Δ columns, labels, and topic names or locked states, in that order. Muted Control (muted-control) is the text of unselected camera segments and the run name in the toolbar.
- **Floor** (floor), **Grid** (grid), **Wall Cell** (wall-cell) and **Driven Path** (driven-path): map materials. Wall cells use the wall colour at an alpha that rises with the evidence count, up to 1 at twelve hits.

### Named Rules

**The Data Owns Colour Rule.** Saturated colour appears only on something the robot produced or something the visitor operates. Panels, headings and borders stay grey.

**The Pink Means Belief Rule.** Odometry pink marks the robot's estimate and its error, and nothing else.

**The Swatch Is The Mark Rule.** Each layer swatch (20x16) is drawn in the same mark the map uses, so the layer list is also the legend.

## Typography

**Body Font:** system-ui (with -apple-system, Segoe UI, sans-serif)
**Label/Mono Font:** JetBrains Mono (weights 400, 500, 600), with tabular figures

**Character:** The system face keeps the chrome familiar, like any developer tool. JetBrains Mono marks anything a machine produced: values, units, topic names, the clock and map labels.

### Hierarchy

- **Title** (600, 15px): the wordmark (set at 700) and the current activity line in the mission card.
- **Heading** (600, 12px, letter-spacing 0.02em): panel headings, tab labels and the Map heading.
- **Body** (400, 13px, 1.35): layer names, objective names, definition lists and buttons.
- **Label** (400, 12px): secondary lines, objective locations and the selected objective note.
- **Chip** (600, 11px): status chips on objectives.
- **Value** (JetBrains Mono 400, 13px or 12px, tabular): pose tables, motion values, the footer and the clock.
- **Topic** (JetBrains Mono 400, 11px): ROS topic names under each layer and secondary heading notes such as "1 m grid".
- **Map Label** (JetBrains Mono 500, 11px): name tags and rack labels drawn on the canvas. Objective numbers in markers use 600 at 10px.

### Named Rules

**The Machine Speaks Mono Rule.** If a value came from the simulation, set it in JetBrains Mono with tabular figures. Words written for people stay in the system face.

**The Topic Under The Name Rule.** On desktop, every layer row shows its plain name with its ROS topic (`/scan`, `/map`, `/odom`) beneath in the topic style.

## Layout

The desktop view is a three-row grid: a 46px toolbar, the workspace and a 40px footer. The workspace has three columns: a 236px layer list, the map, and a 340px inspector. The columns sit on a Rule background with a 1px gap, so the gaps draw the dividers. The map stage fills its column and has a slim header row holding the "Map" heading and the camera switch.

Spacing runs on a 12px gutter (panel padding, card margins, list insets), with 14px in the toolbar and footer, and 8px, 10px and 4px inside rows. Tabs are 38px tall and phone layer chips 34px. Layer and objective rows take the height of their two lines.

When the console is narrower than 760px (measured on the root element), the layout becomes one column: the map first (at least 300px tall), then layer chips in a wrapping row with short names, then the tabbed inspector at 452px. The toolbar drops the run name and clock, the status pill shortens "simulated" to "sim", and the camera card starts closed.

The map has three cameras: Follow robot (default, centred on the true pose and interpolated at 20 Hz), Whole map, and Robot POV. The overview canvas in the Mission tab shows the follow frame or the POV view cone.

### Named Rules

**The Hairline Grid Rule.** Panels are separated by 1px Rule lines made from the grid gap, never by spacing or shadow alone.

**The Unseen Is Blank Rule.** Space the robot has not scanned stays plain Canvas. Floor, walls and objectives appear only after the lidar has seen them.

## Elevation & Depth

The interface is flat. No `box-shadow` appears anywhere in the build. Depth comes from three tonal steps (Canvas, Panel, Chrome) and from the 1px rules between them. The one floating element, the Robot POV camera card, uses a translucent panel (`rgba(15,18,23,0.92)`) with an Edge border.

Robot POV is the only 3D view. It draws the occupancy map as 0.25m blocks extruded to 1.4m, because a 2D lidar has no height. Wall faces are shaded from the wall colour over Canvas, with a fill factor of `min(1, (0.12 + 0.18k) × light × fog)`, where k is the block's evidence and light is 0.72 for faces that point along x, 0.95 for faces along y and 1.15 for tops. Faces stay well below the brightness of the type, and each vertical face gets a faint top edge highlight (`rgba(230,234,240,0.45 × fog)`).

### Named Rules

**The Flat Console Rule.** Surfaces never cast shadows. A layer above another is shown by a step in tone and a hairline.

**The Honest Height Rule.** POV walls are extruded to a fixed 1.4m and labelled as such, because the sensor gives no height.

## Shapes

Corners are small and functional: 3px on progress bars and run segments, 4px on camera segments, 5px on buttons and phone chips, 6px on cards and the camera group, and full pills on status chips and the status pill. The robot body is a rounded rectangle (1m by 0.72m, 0.12m radius). Objective markers are diamonds (14px squares rotated 45°) carrying a mono number. Borders are always 1px and run all the way around. The two thicker strokes are the 2px tab underline and the 3px top bar on each step of the phase stepper.

## Components

### Buttons

- **Shape:** gently rounded (5px).
- **Secondary (Pause / Resume):** Raised fill, Ink text, 1px Edge Strong border, 30px tall with 12px side padding. The label says it pauses your view, and the aria label says the same.
- **Hover / Focus:** hover raises brightness to 1.25 with no transition. Focus shows a 2px Plan Blue outline offset 2px.
- **Text link (Reset):** Plan Blue text on transparent, no border.

### Segmented control (camera switch)

- **Style:** a 1px Edge outlined group with 6px corners and 2px inner padding, holding 26px segments with 4px corners.
- **State:** the selected segment fills with Segment Selected and uses Ink text. Others are transparent with Muted text. Each segment exposes `aria-pressed`.

### Tabs

- **Style:** three equal tabs (Mission, Robot, Lidar), 38px tall, in the heading style.
- **State:** the selected tab has Ink text and a 2px Plan Blue bottom border. Others have Muted text and no border.

### Chips

- **Status chips:** pill shape, 1px border, 11px semibold. Locked uses Faint text and an Edge border. Queued uses Plan Blue text and a Queued Edge border. Active fills Plan Blue with Canvas text. Done uses Signal Green text and a Done Edge border.
- **Status pill (toolbar):** pill with an 8px dot. It reads "Live · simulated · phase" with a green dot, Live Ink text and a Live Edge border, or "Paused · simulated · phase" with a Faint dot, Text Secondary text and an Edge border.

### Cards / Containers

- **Corner Style:** 6px.
- **Background:** Chrome.
- **Shadow Strategy:** none, per the Flat Console Rule.
- **Border:** 1px Rule.
- **Internal Padding:** 10px 12px. Used for the current activity card and the selected objective note.

### Navigation (layer list)

- **Desktop rows:** a 16px checkbox (3px corners, Raised fill, Edge Strong stroke, Plan Blue tick), a 20x16 swatch, then the name with its topic. A hidden layer fades its swatch and text to 45% opacity.
- **Phone chips:** 34px chips with Chrome fill, Edge border and 5px corners, carrying the swatch and a short name.

### Objective list

- **Rows:** a mono number, the name with its location below, and a status chip on the right. Locked rows dim to 55%.
- **Selected:** the row fills with Row Selected and the number turns Plan Blue. A note card below explains why the objective is locked, queued, active or done.

### Phase stepper and run progress

- **Stepper:** three steps (Map, Objectives, Complete), each with a 3px top bar: green when done, blue when current, Edge when pending.
- **Footer segments:** 6px tracks with 3px corners on Rule, one double-width mapping segment and one per objective, filled blue while running and green when done.

### Map marks (signature)

- **Lidar:** amber points 1.9px in radius, replaced every turn, with a hairline sweep head at 75% opacity. The scan runs at 2 Hz.
- **Plan:** blue. Dashed (7/5) at 1.75px during the mapping survey, solid at 2.5px with waypoint dots for planned objective paths.
- **Robot:** true pose as an Ink outline over a 10% Ink fill with red and green TF axes. The odometry estimate is a dashed pink footprint, joined to the truth by a pink line once they drift more than 8cm apart.
- **Name tags:** mono labels on a filled tag, moved clear of the robot with a 1px leader line when they would overlap it.

## Do's and Don'ts

### Do:

- **Do** keep each data colour on its topic: amber for `/scan`, blue for `/plan` and `/goals`, pink for `/odom`, red and green for `/tf` axes.
- **Do** set every simulation value in JetBrains Mono with tabular figures.
- **Do** draw dividers as 1px Rule (#222730) hairlines.
- **Do** draw the plan dashed during the mapping survey and solid for planned objective paths.
- **Do** leave unscanned space blank and show objectives only once their spot is mapped.
- **Do** label the run as simulated in the status pill until real runs exist.
- **Do** open paused when the visitor prefers reduced motion, and move without fades.

### Don't:

- **Don't** add shadows or glows to panels, cards or controls.
- **Don't** use coloured side-stripe borders to mark a selected row or a callout. Use the Row Selected tint and a blue number, or a 1px card.
- **Don't** use Unicode glyphs as icons. Chevrons and checks are inline SVG.
- **Don't** add illustration, mascots or decorative chrome to the console.
- **Don't** offer any control that changes the shared simulation. Visitor controls change only the visitor's own view.
- **Don't** draw a state the simulation did not produce. Interpolating between two real 20 Hz ticks is the only smoothing allowed.
