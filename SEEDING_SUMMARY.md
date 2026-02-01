# Inventory Seeding Summary

## Current Status

The seeding script has been updated with the correct SKU format:

### Parent Item SKUs
- **Format**: Simple numeric (1, 2, 3, 4, ...)
- **Per Item Type**: Each parent item type has its own counter
- **Examples**:
  - Sports Tower: SKUs 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
  - Clinical 1788: SKUs 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
  - RISE Tower: SKUs 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
  - MedEd 1788: SKUs 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
  - MedEd 1688: SKUs 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
  - 1788 Roll Stand: SKUs 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
  - 1688 Roll Stand: SKUs 1, 2, 3, 4, 5, 6, 7, 8, 9, 10

### Child Item SKUs
- **Format**: Serial number style (e.g., 2204FE3842)
- **Pattern**: 4 random digits + 6 random hex characters
- **Examples**: 
  - 3847A2B4C9
  - 1205F3E8D2
  - 9234B7A1F6

## Script: `scripts/reseed_complete_inventory.py`

### What It Does

1. **Clears existing inventory** - Deletes all parent items (cascades to child items)
2. **Creates item types** - Ensures all 7 parent and 19 child item types exist
3. **Sets up locations** - Creates 5 hospital locations (Hospital A-E)
4. **Creates inventory**:
   - 10 of each parent item type (70 total parent items)
   - 8 in warehouses
   - 1 at first client site
   - 1 in quarantine
   - Each with appropriate child items per configuration
5. **Moves items to hospitals** - 3 items to each hospital
6. **Creates movement history** - 30 additional random movements

### Configuration

Each parent item type gets specific child items:

- **Sports Tower**: Crossfire, Crossflow, random Light Source, Vision Pro Monitor
- **MedEd 1688**: 1688 CCU, L11, Pneumoclear, OLED, optional OR Hub
- **MedEd 1788**: 1788 CCU, L12, Pneumoclear, optional OR Hub
- **Clinical 1788**: OR Hub, 1788 CCU, L12, Printer, Pinpoint, OLED
- **RISE Tower**: OR Hub, 1688 CCU, L11, Printer, Pinpoint
- **1788 Roll Stand**: Pole, Base, OLED
- **1688 Roll Stand**: Pole, Base

### Timing

- 2 second delay between child item creations
- 2 second delay between parent item creations
- 1.5 second delay between movements
- Total estimated time: ~45-60 minutes

### Expected Results

- **Parent Items**: 70 (7 types × 10 each)
- **Child Items**: ~200-250 (varies due to optional components)
- **Movements**: ~45-60 (15 to hospitals + 30 additional)
- **Hospitals**: 5 new client site locations

## How to Run

```bash
# Stop any currently running script (Ctrl+C)

# Run the updated script
python scripts/reseed_complete_inventory.py 2>&1 | Tee-Object -FilePath reseed_output.log
```

## Verification

After completion, check:
1. Parent items have simple numeric SKUs (1-10 per type)
2. Child items have serial number format SKUs
3. Items are distributed across warehouses, client sites, and quarantine
4. Movement history exists
5. 5 hospital locations created

## Notes

- The script uses the unique constraint on SKUs - duplicates will be rejected
- Connection pool is limited to 5+10, so 2-second delays prevent exhaustion
- Rate limit is 300 requests per 60 seconds - script stays well under this
