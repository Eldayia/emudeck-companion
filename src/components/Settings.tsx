import { ButtonItem, PanelSection, PanelSectionRow, SliderField, ToggleField } from "@decky/ui";
import type { CompanionSettings, EmulatorSession } from "../types";

interface Props {
  settings: CompanionSettings;
  session: EmulatorSession | null;
  onChange: (changes: Partial<CompanionSettings>) => Promise<void>;
}

export function Settings({ settings, session, onChange }: Props) {
  const favorites = session ? (settings.favorites[session.emulator] ?? []) : [];
  const availableActions = session
    ? session.available_capabilities.filter((action) => Boolean(session.actions[action]))
    : [];
  const gameOverride = session?.game_key ? settings.game_overrides[session.game_key] : undefined;
  const hiddenActions = gameOverride?.hidden_actions ?? [];

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

  const toggleGameAction = (action: string, visible: boolean) => {
    if (!session?.game_key) return Promise.resolve();
    const hidden = visible
      ? hiddenActions.filter((item) => item !== action)
      : [...hiddenActions, action].filter((item, index, values) => values.indexOf(item) === index);
    const overrides = { ...settings.game_overrides };
    if (hidden.length > 0) overrides[session.game_key] = { hidden_actions: hidden };
    else delete overrides[session.game_key];
    return onChange({ game_overrides: overrides });
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
      {session?.game_key && availableActions.length > 0 && (
        <PanelSection title={`Game Overrides — ${session.game ?? "Current Game"}`}>
          {availableActions.map((action) => (
            <ToggleField
              key={action}
              label={session.actions[action].label}
              description="Show this action for this game"
              checked={!hiddenActions.includes(action)}
              onChange={(visible) => void toggleGameAction(action, visible)}
            />
          ))}
          {hiddenActions.length > 0 && (
            <PanelSectionRow>
              <ButtonItem
                layout="below"
                onClick={() => void onChange({
                  game_overrides: Object.fromEntries(
                    Object.entries(settings.game_overrides).filter(([key]) => key !== session.game_key),
                  ),
                })}
              >
                Reset Game Overrides
              </ButtonItem>
            </PanelSectionRow>
          )}
        </PanelSection>
      )}
    </>
  );
}
