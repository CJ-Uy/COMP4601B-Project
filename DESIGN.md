---
name: Compact reasoning
description: A clear visual research document for readers new to language models.
colors:
  ink: "#132d4f"
  muted: "#4c6079"
  blue: "#164dcf"
  ice: "#e9f2ff"
  line: "#c7d7ec"
  teal: "#086858"
  amber: "#7a4800"
  paper: "#fff"
  soft: "#f4f8fe"
typography:
  display:
    fontFamily: 'Atkinson, "Segoe UI", sans-serif'
    fontSize: "clamp(2rem, 3.5vw, 3.1rem)"
    fontWeight: 700
    lineHeight: 1.13
    letterSpacing: "-0.025em"
  headline:
    fontFamily: 'Atkinson, "Segoe UI", sans-serif'
    fontSize: "clamp(1.9rem, 3vw, 2.65rem)"
    fontWeight: 700
    lineHeight: 1.13
    letterSpacing: "-0.025em"
  body:
    fontFamily: 'Atkinson, "Segoe UI", sans-serif'
    fontSize: "18px"
    fontWeight: 400
    lineHeight: 1.55
rounded:
  control: "6px"
  figure: "8px"
  node: "14px"
  sheet: "20px"
spacing:
  compact: "0.5rem"
  normal: "1rem"
  generous: "2rem"
components:
  diagram-button:
    backgroundColor: "{colors.soft}"
    textColor: "{colors.ink}"
    rounded: "{rounded.node}"
    padding: "1rem 1.15rem"
  diagram-button-hover:
    backgroundColor: "{colors.ice}"
  navigation-button:
    backgroundColor: "{colors.ice}"
    textColor: "{colors.blue}"
    rounded: "{rounded.control}"
    padding: "0.45rem 0.7rem"
---

# Design System: Compact reasoning

## Overview

**Creative North Star: "Interactive mathematics exhibit"**

The interface uses clear type, exact diagrams and generous space to make unfamiliar research understandable. Figures carry relationships; short labels identify the parts. Detailed reading remains available through explicit controls.

White and pale blue form the reading ground. Navy anchors the text, cobalt identifies interaction, and restrained semantic colors distinguish parts of a comparison. The design supports both visual explanation and honest progress reporting.

**Key Characteristics:**

- Precise geometric diagrams with consistent strokes.
- Readable lettering and clear control states.
- Additional detail appears on demand.

## Colors

Cobalt is the primary interaction color. Teal supports learning and verified status; amber supports planned settings and the original-solution baseline. Navy, muted blue, white and pale surfaces organize reading. Color is always accompanied by a label.

**The Label Rule.** A status, data group or comparison remains identifiable without its color.

## Typography

Display and body text use self-hosted Atkinson Hyperlegible, with Segoe UI and sans-serif fallbacks. Bold headings and ordinary body weight carry the hierarchy. Mobile body text becomes 17px below 700px. The infographic title becomes 2.5rem below 850px and 2.2rem below 480px. Longer reading introductions use a measure of up to 72 characters.

## Layout

Content sits inside a 1260px maximum width. The infographic uses a two-to-one column relationship, narrowing at 1050px and stacking at 850px. The data figures use two columns on intermediate screens and stack below 480px. Major reading sections use 4.5rem vertical padding; related controls and figures stay closer together.

Detailed reading appears in a drawer up to 560px wide on desktop. At 850px and below it becomes an 80dvh bottom sheet with space above it and safe-area padding below. The document stays in position while the dialog scrolls independently.

## Elevation & Depth

The infographic is flat at rest. Pale fills, thin borders and clear grouping create depth. A translucent navy backdrop separates an open dialog from the document. The selected diagram node uses an inset cobalt stroke, and keyboard focus uses a three-pixel outline with a four-pixel offset.

## Shapes

Infographic nodes use gently curved corners. Smaller figures and controls have tighter corners, while the mobile sheet has rounded upper corners. Circular stage markers and crisp line arrows express sequence. SVG draws exact geometric diagrams.

## Components

Diagram buttons expose a whole figure as a single target, with a hover tint and an active stroke. Detail-level buttons use pressed states; Previous and Next become disabled at the sequence boundaries. The close control is 44px square.

Native dialog behavior provides keyboard focus, Escape dismissal and focus return. Content changes return the dialog to the beginning. The drawer and sheet enter over 0.32 seconds using the shared easing curve. A 0.3-second content reveal uses a small translation, clipping and blur. Reduced motion removes these animations.

Native selects and range controls support the demonstrations and result filters. Collapsible references keep additional material reachable. Navigation, selection, focus, caret and scrollbars use the same palette. Loading, error and empty states describe the available research evidence accurately.

## Do's and Don'ts

### Do

- Do pair color with an explicit label.
- Do use the existing geometric SVG stroke system.
- Do preserve visible keyboard focus and reduced-motion behavior.
- Do identify illustrative figures and provisional settings.

### Don't

- Don't replace the infographic with a wall of paragraphs.
- Don't present illustrative values as measured results.
- Don't use a decoration in place of an explanatory figure.
