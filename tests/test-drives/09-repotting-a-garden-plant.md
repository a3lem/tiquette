# A non-coding example: repotting a garden plant


## Setup

Empty tickets directory

## Steps:

1. Create tickets from this text:

  ```plain
  Repotting a plant is an important part of keeping it healthy and encouraging continued growth. Begin by choosing a new pot that is slightly larger than the current one, ensuring it has drainage holes at the bottom to prevent waterlogging. Prepare a layer of fresh potting mix at the base of the new pot. Carefully remove the plant from its old container by gently squeezing the sides and tipping it out, supporting the base of the stem with your hand. Shake away any loose soil from the roots and inspect them, trimming any that appear brown, soft, or damaged. Place the plant in the centre of the new pot and fill in the gaps around it with fresh potting mix, pressing it down lightly to remove air pockets. Finally, water the plant thoroughly and place it in a suitable location to recover. Most plants benefit from repotting every one to two years, ideally in spring when growth is most active.
  ```

2. Run any other commands required to get everything ready for execution.

## What to watch for

### Dependencies

Ticket dependencies should roughly match the following:

```
Choose new pot – no dependencies
Prepare base layer – blocked by: Choose new pot
Remove plant from old container – no dependencies
Inspect and trim roots – blocked by: Remove plant
Place plant in new pot – blocked by: Choose new pot, Prepare base layer, Inspect and trim roots
Fill and press down potting mix – blocked by: Place plant in new pot
Water thoroughly – blocked by: Fill and press down potting mix
```
  
