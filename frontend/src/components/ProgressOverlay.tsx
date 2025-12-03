import React, { Dispatch, SetStateAction, useEffect, useState } from "react";

interface Props {
  progress: {
    visible: boolean;
    label: string;
    currentStep: number;
    totalSteps: number;
    famlyTarget: number;
    babyTarget: number;
  };
}

export const ProgressOverlay: React.FC<Props> = ({ progress }) => {
  const [famlyDisplay, setFamlyDisplay] = useState(0);
  const [babyDisplay, setBabyDisplay] = useState(0);

  useEffect(() => {
    if (!progress.visible) return;
    setFamlyDisplay(0);
    setBabyDisplay(0);
  }, [progress.visible, progress.label]);

  const animateTo = (
    target: number,
    setFn: Dispatch<SetStateAction<number>>,
  ) => {
    setFn((current) => {
      if (current === target) return current;
      const diff = target - current;
      const step = Math.max(1, Math.round(diff / 5));
      const next = current + step;
      if ((diff > 0 && next > target) || (diff < 0 && next < target)) {
        return target;
      }
      return next;
    });
  };

  useEffect(() => {
    if (!progress.visible) return;
    const interval = setInterval(() => {
      animateTo(progress.famlyTarget, setFamlyDisplay);
      animateTo(progress.babyTarget, setBabyDisplay);
    }, 100);
    return () => clearInterval(interval);
  }, [progress.visible, progress.famlyTarget, progress.babyTarget]);

  if (!progress.visible) return null;

  const percentage =
    progress.totalSteps > 0
      ? Math.min(
          100,
          Math.round((progress.currentStep / progress.totalSteps) * 100),
        )
      : 0;

  return (
    <div className="progress-overlay">
      <div className="progress-panel">
        <h3>Scraping data</h3>
        <p className="progress-panel__label">{progress.label}</p>
        <div className="progress-bar">
          <div
            className="progress-bar__fill"
            style={{ width: `${percentage}%` }}
          />
        </div>
        <div className="progress-stats">
          <div>
            <p>Famly entries</p>
            <strong>{famlyDisplay}</strong>
          </div>
          <div>
            <p>Baby Connect entries</p>
            <strong>{babyDisplay}</strong>
          </div>
        </div>
      </div>
    </div>
  );
};
