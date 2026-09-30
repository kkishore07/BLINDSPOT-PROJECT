using UnityEngine;

public class BlindSpotDetector : MonoBehaviour
{
    public BlindSpotManager safetyManager;

    private void OnTriggerEnter(Collider other)
    {
        if (!other.CompareTag("Worker"))
            return;

        if (safetyManager != null)
        {
            safetyManager.workerInsideBlindSpot = true;
        }

        Debug.Log("BLIND SPOT: WORKER DETECTED");
    }

    private void OnTriggerStay(Collider other)
    {
        if (!other.CompareTag("Worker"))
            return;

        if (safetyManager != null)
        {
            safetyManager.workerInsideBlindSpot = true;
        }
    }

    private void OnTriggerExit(Collider other)
    {
        if (!other.CompareTag("Worker"))
            return;

        if (safetyManager != null)
        {
            safetyManager.workerInsideBlindSpot = false;
        }

        Debug.Log("BLIND SPOT: WORKER LEFT");
    }
}