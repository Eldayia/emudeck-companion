import { PanelSection, SliderField, ToggleField } from "@decky/ui";
import type { CompanionSettings, EmulatorSession } from "../types";

interface Props {
  settings: CompanionSettings;
  session: EmulatorSession | null;
  onChange: (changes: Partial<CompanionSettings>) => Promise<void>;
}

export function Settings({ settings, session, onChange }: Props) {
  const favorites = session ? (settings.favorites[session.emulator] ?? []) : [];
  const availableActions = session
    ? session.capabilities.filter((action) => Boolean(session.actions[action]))
    : [];

  const toggleFavorite = (action: string, checked: boolean) => {
    const selected = checked
      ? [...favorites, action].filter((item, index, values) => values.indexOf(item) === index).slice(0, 4)
      : favorites.filter((item) => item !== action);
    return onChange({
      favorites: {
        ...settings.favorites,
        ...(session ? { [session.emulator]: selected } : {}),
      },
    });
  };

  return (
    <>
      <PanelSection title="Settings">
        <ToggleField
          label="Action notifications"
          description="Show a notification after successful actions"
          checked={settings.notifications}
          onChange={(checked) => void onChange({ notifications: checked })}
        />
        <ToggleField
          label="Show platform"
          checked={settings.show_platform}
          onChange={(checked) => void onChange({ show_platform: checked })}
        />
        <ToggleField
          label="Show emulator"
          checked={settings.show_emulator}
          onChange={(checked) => void onChange({ show_emulator: checked })}
        />
        <ToggleField
          label="Show session time"
          checked={settings.show_session_time}
          onChange={(checked) => void onChange({ show_session_time: checked })}
        />
        <SliderField
          label="Detection interval"
          description="How often Companion checks the active emulator"
          value={settings.detection_interval_ms}
          min={1000}
          max={5000}
          step={250}
          showValue
          valueSuffix=" ms"
          onChange={(value) => void onChange({ detection_interval_ms: value })}
        />
      </PanelSection>
      {session && availableActions.length > 0 && (
        <PanelSection title={`Favorites — ${session.emulator_name}`}>
          {availableActions.map((action) => {
            const checked = favorites.includes(action);
            return (
              <ToggleField
                key={action}
                label={session.actions[action].label}
                description={checked ? "Shown in Favorites" : ""}
                checked={checked}
                disabled={!checked && favorites.length >= 4}
                onChange={(value) => void toggleFavorite(action, value)}
              />
            );
          })}
        </PanelSection>
      )}
    </>
  );
}
