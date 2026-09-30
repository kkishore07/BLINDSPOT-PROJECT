using UnityEngine;
using UnityEngine.InputSystem;

public class WorkerController : MonoBehaviour
{
    public float walkingSpeed = 3f;
    public float rotationSpeed = 180f;

    public bool manualControl = true;

    void Update()
    {
        if (!manualControl)
            return;

        if (Keyboard.current == null)
            return;

        float forward = 0f;
        float turn = 0f;

        // W / S
        if (Keyboard.current.wKey.isPressed)
            forward = 1f;

        if (Keyboard.current.sKey.isPressed)
            forward = -1f;

        // A / D
        if (Keyboard.current.aKey.isPressed)
            turn = -1f;

        if (Keyboard.current.dKey.isPressed)
            turn = 1f;

        // Rotate worker
        transform.Rotate(
            Vector3.up,
            turn * rotationSpeed * Time.deltaTime
        );

        // Move worker
        transform.position +=
            transform.forward *
            forward *
            walkingSpeed *
            Time.deltaTime;
    }
}