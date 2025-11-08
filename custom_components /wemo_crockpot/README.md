# WeMo Crockpot Custom Integration for Home Assistant

This custom integration provides full control of your WeMo Crockpot in Home Assistant, including mode selection and built-in timer control.

## Features

- **Mode Selection**: Select between Off, Warm, Low, and High cooking modes using a dropdown
- **Built-in Timer**: Set the Crockpot's built-in timer (0-1440 minutes / 24 hours)
- **Sensors**: Monitor current mode, remaining time, and cooked time
- **Real-time Updates**: Automatic polling every 30 seconds to keep state in sync

## Installation

### Manual Installation

1. Copy the `wemo_crockpot` folder to your Home Assistant's `custom_components` directory:
   ```
   <config_directory>/custom_components/wemo_crockpot/
   ```

2. Restart Home Assistant

3. Go to **Settings** → **Devices & Services** → **Add Integration**

4. Search for "WeMo Crockpot" and follow the setup wizard

5. Enter your Crockpot's IP address when prompted

## Entities

Once configured, you'll have the following entities:

### Sensors
- **sensor.wemo_crockpot_mode** - Current cooking mode
- **sensor.wemo_crockpot_remaining_time** - Time remaining on timer (minutes)
- **sensor.wemo_crockpot_cooked_time** - Time already cooked (minutes)

### Controls
- **select.wemo_crockpot_cooking_mode** - Dropdown to select cooking mode
- **number.wemo_crockpot_timer** - Slider/input to set timer (0-1440 minutes)

## Usage Examples

### Using the Built-in Timer (Recommended)

The Crockpot has its own built-in timer that automatically turns off when time expires.

**Set to cook on Low for 8 hours:**
```yaml
service: select.select_option
target:
  entity_id: select.wemo_crockpot_cooking_mode
data:
  option: "Low"
---
service: number.set_value
target:
  entity_id: number.wemo_crockpot_timer
data:
  value: 480  # 8 hours = 480 minutes
```

### Using Home Assistant Automations

**Multi-stage cooking - High for 2 hours, then Warm:**
```yaml
automation:
  - alias: "Crockpot: High to Warm"
    trigger:
      - platform: time
        at: "10:00:00"
    action:
      - service: select.select_option
        target:
          entity_id: select.wemo_crockpot_cooking_mode
        data:
          option: "High"
      - delay:
          hours: 2
      - service: select.select_option
        target:
          entity_id: select.wemo_crockpot_cooking_mode
        data:
          option: "Warm"
```

**Auto shutoff after 6 hours:**
```yaml
automation:
  - alias: "Crockpot: Auto shutoff"
    trigger:
      - platform: state
        entity_id: select.wemo_crockpot_cooking_mode
        to: "Low"
    condition:
      - condition: numeric_state
        entity_id: sensor.wemo_crockpot_remaining_time
        below: 1
    action:
      - delay:
          hours: 6
      - service: select.select_option
        target:
          entity_id: select.wemo_crockpot_cooking_mode
        data:
          option: "Off"
```

## Built-in Timer vs Automations

| Feature | Built-in Timer | HA Automations |
|---------|---------------|----------------|
| **Reliability** | ✅ Works offline | ❌ Requires HA running |
| **Simplicity** | ✅ One-step | ⚠️ Needs automation |
| **Multi-stage** | ❌ Single timer | ✅ Unlimited flexibility |
| **Notifications** | ❌ No | ✅ Yes |

**Recommendation**: Use built-in timer for simple cooking, automations for complex scenarios.
