import { useEffect, useMemo, useState } from 'react';
import './TimeControl.css';

const getDateKey = (timestamp) => timestamp.slice(0, 10);

const formatDate = (dateKey) => {
  const date = new Date(`${dateKey}T00:00:00Z`);
  if (Number.isNaN(date.getTime())) return dateKey;
  return new Intl.DateTimeFormat('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(date);
};

const formatTime = (timestamp) => {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return timestamp;
  return `${new Intl.DateTimeFormat('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
    timeZone: 'UTC',
  }).format(date)} UTC`;
};

export default function TimeControl({ timestamps, selectedTime, onChange, loading }) {
  const [playing, setPlaying] = useState(false);
  const [selectedDate, setSelectedDate] = useState(getDateKey(selectedTime));
  const groupedTimestamps = useMemo(() => timestamps.reduce((groups, timestamp) => {
    const dateKey = getDateKey(timestamp);
    groups[dateKey] = [...(groups[dateKey] || []), timestamp];
    return groups;
  }, {}), [timestamps]);
  const dates = useMemo(() => Object.keys(groupedTimestamps).sort(), [groupedTimestamps]);
  const currentDate = dates.includes(selectedDate) ? selectedDate : getDateKey(selectedTime);
  const dateTimestamps = groupedTimestamps[currentDate] || [selectedTime];
  const selectedIndex = Math.max(0, dateTimestamps.indexOf(selectedTime));
  const globalIndex = Math.max(0, timestamps.indexOf(selectedTime));
  const hasPrevious = globalIndex > 0;
  const hasNext = globalIndex < timestamps.length - 1;

  useEffect(() => {
    setSelectedDate(getDateKey(selectedTime));
  }, [selectedTime]);

  useEffect(() => {
    if (!playing || !hasNext) {
      if (playing && !hasNext) setPlaying(false);
      return undefined;
    }

    const timer = window.setInterval(() => {
      const nextIndex = timestamps.indexOf(selectedTime) + 1;
      if (nextIndex >= timestamps.length) {
        setPlaying(false);
        return;
      }
      onChange(timestamps[nextIndex]);
    }, 1500);

    return () => window.clearInterval(timer);
  }, [hasNext, onChange, playing, selectedTime, timestamps]);

  const moveBy = (offset) => {
    const nextIndex = Math.min(Math.max(globalIndex + offset, 0), timestamps.length - 1);
    onChange(timestamps[nextIndex]);
  };

  const changeDate = (dateKey) => {
    setPlaying(false);
    setSelectedDate(dateKey);
    const firstTimestamp = groupedTimestamps[dateKey]?.[0];
    if (firstTimestamp) onChange(firstTimestamp);
  };

  return (
    <section className="time-control glass-panel" aria-label="Time exploration">
      <div className="time-control__topline">
        <span className="time-control__eyebrow">Time exploration · UTC</span>
        <strong>{formatDate(currentDate)}</strong>
      </div>
      <div className="time-control__date-row">
        <label htmlFor="time-date">Date</label>
        <select id="time-date" value={currentDate} onChange={(event) => changeDate(event.target.value)} disabled={!dates.length}>
          {dates.map((dateKey) => <option key={dateKey} value={dateKey}>{formatDate(dateKey)}</option>)}
        </select>
        <span className="time-control__selected-time">{formatTime(selectedTime)}</span>
      </div>
      <div className="time-control__actions">
        <button type="button" onClick={() => moveBy(-1)} disabled={!hasPrevious} aria-label="Previous timestep">‹</button>
        <button type="button" className="time-control__play" onClick={() => setPlaying((current) => !current)} disabled={!timestamps.length} aria-label={playing ? 'Pause playback' : 'Play playback'}>
          {playing ? 'Ⅱ' : '▶'}
        </button>
        <button type="button" onClick={() => moveBy(1)} disabled={!hasNext} aria-label="Next timestep">›</button>
        <span className="time-control__count">{globalIndex + 1} / {timestamps.length}</span>
      </div>
      <input
        className="time-control__slider"
        type="range"
        min="0"
        max={Math.max(dateTimestamps.length - 1, 0)}
        step="1"
        value={selectedIndex}
        onChange={(event) => {
          setPlaying(false);
          onChange(dateTimestamps[Number(event.target.value)]);
        }}
        aria-label="Select available UTC time for selected date"
        disabled={!dateTimestamps.length}
      />
      <div className="time-control__ticks" aria-hidden="true">
        {dateTimestamps.map((timestamp) => <span key={timestamp} title={formatTime(timestamp)} />)}
      </div>
      {loading && <span className="time-control__status">Updating ocean state…</span>}
    </section>
  );
}
