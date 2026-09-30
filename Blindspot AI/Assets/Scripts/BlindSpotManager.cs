using UnityEngine;
using TMPro;

public class BlindSpotManager : MonoBehaviour
{
    [Header("Objects")]
    public Transform excavator;
    public Transform worker;

    [Header("UI")]
    public TMP_Text distanceText;
    public TMP_Text riskText;
    public TMP_Text speedText;
    public TMP_Text alertText;

    [Header("Safety Zones")]
    public float warningDistance = 10f;
    public float dangerDistance = 5f;
    public float criticalDistance = 2f;

    [Header("Excavator")]
    public ExcavatorController excavatorController;
    public AutoExcavatorWork autoExcavatorWork;

    [Header("Safety State")]
    public bool workerDetected = false;
    public bool emergencyStop = false;

    private float distance;
    public bool workerInsideBlindSpot = false;
    private float allowedSpeed = 100f;

    void Update()
    {
        if (excavator == null || worker == null)
            return;

        distance = Vector3.Distance(
            excavator.position,
            worker.position
        );

        UpdateSafetyState();
        UpdateDashboard();
    }

    void UpdateSafetyState()
    {
        // Worker is outside the monitored blind-spot area
        if (!workerInsideBlindSpot)
        {
            workerDetected = false;
            emergencyStop = false;
            allowedSpeed = 100f;
        }
        else
        {
            // Worker is inside the monitored area
            workerDetected = true;

            // CRITICAL
            if (distance <= criticalDistance)
            {
                emergencyStop = true;
                allowedSpeed = 0f;
            }
            // DANGER
            else if (distance <= dangerDistance)
            {
                emergencyStop = false;
                allowedSpeed = 40f;
            }
            // WARNING
            else if (distance <= warningDistance)
            {
                emergencyStop = false;
                allowedSpeed = 70f;
            }
            // Inside zone but far enough away
            else
            {
                emergencyStop = false;
                allowedSpeed = 100f;
            }
        }

        // Manual excavator controller
        if (excavatorController != null)
        {
            excavatorController.safetySpeedMultiplier =
                allowedSpeed / 100f;

            excavatorController.emergencyStop =
                emergencyStop;
        }

        // Automatic excavator controller
        if (autoExcavatorWork != null)
        {
            autoExcavatorWork.safetySpeedMultiplier =
                allowedSpeed / 100f;

            autoExcavatorWork.emergencyStop =
                emergencyStop;
        }
    }

    void UpdateDashboard()
    {
        if (distanceText != null)
        {
            distanceText.text =
                "Distance: " +
                distance.ToString("F1") +
                " m";
        }

        if (speedText != null)
        {
            speedText.text =
                "Machine Speed: " +
                allowedSpeed.ToString("F0") +
                "%";
        }

        if (riskText != null)
        {
            if (distance > warningDistance)
                riskText.text = "Risk Level: SAFE";

            else if (distance > dangerDistance)
                riskText.text = "Risk Level: WARNING";

            else if (distance > criticalDistance)
                riskText.text = "Risk Level: DANGER";

            else
                riskText.text = "Risk Level: CRITICAL";
        }

        if (alertText != null)
        {
            if (distance <= criticalDistance)
            {
                alertText.text =
                    "EMERGENCY STOP\n" +
                    "WORKER TOO CLOSE";
            }
            else if (distance <= dangerDistance)
            {
                alertText.text =
                    "ALERT: ACTIVE";
            }
            else
            {
                alertText.text =
                    "ALERT: OFF";
            }
        }
    }
}