using UnityEngine;
using UnityEngine.InputSystem;

public class ExcavatorController : MonoBehaviour
{
    [Header("Normal Movement")]
    public float moveSpeed = 5f;
    public float rotationSpeed = 40f;

    [Header("Safety System")]
    public float safetySpeedMultiplier = 1f;
    public bool emergencyStop = false;

    void Update()
    {
        if (Keyboard.current == null)
            return;

        // SAFETY STOP
        if (emergencyStop)
            return;

        float moveInput = 0f;
        float turnInput = 0f;

        if (Keyboard.current.wKey.isPressed)
            moveInput = 1f;

        if (Keyboard.current.sKey.isPressed)
            moveInput = -1f;

        if (Keyboard.current.aKey.isPressed)
            turnInput = -1f;

        if (Keyboard.current.dKey.isPressed)
            turnInput = 1f;

        float currentSpeed =
            moveSpeed * safetySpeedMultiplier;

        // Your model's forward direction is local RIGHT
        transform.position +=
            transform.right *
            moveInput *
            currentSpeed *
            Time.deltaTime;

        transform.Rotate(
            Vector3.up,
            turnInput *
            rotationSpeed *
            safetySpeedMultiplier *
            Time.deltaTime
        );
    }
}