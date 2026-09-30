using UnityEngine;
using UnityEngine.InputSystem;

public class ExcavatorArmController : MonoBehaviour
{
    [Header("Excavator Parts")]
    public Transform mainBoom;
    public Transform arm;
    public Transform bucket;

    [Header("Movement Speed")]
    public float boomSpeed = 25f;
    public float armSpeed = 30f;
    public float bucketSpeed = 35f;

    [Header("Angle Limits")]
    public float boomMin = -20f;
    public float boomMax = 60f;

    public float armMin = -60f;
    public float armMax = 40f;

    public float bucketMin = -80f;
    public float bucketMax = 40f;

    private float boomAngle;
    private float armAngle;
    private float bucketAngle;

    void Start()
    {
        if (mainBoom != null)
            boomAngle = mainBoom.localEulerAngles.x;

        if (arm != null)
            armAngle = arm.localEulerAngles.x;

        if (bucket != null)
            bucketAngle = bucket.localEulerAngles.x;
    }

    void Update()
    {
        if (Keyboard.current == null)
            return;

        // Q / E = Boom
        float boomInput = 0f;

        if (Keyboard.current.qKey.isPressed)
            boomInput = 1f;

        if (Keyboard.current.eKey.isPressed)
            boomInput = -1f;

        // R / F = Arm
        float armInput = 0f;

        if (Keyboard.current.rKey.isPressed)
            armInput = 1f;

        if (Keyboard.current.fKey.isPressed)
            armInput = -1f;

        // Z / X = Bucket
        float bucketInput = 0f;

        if (Keyboard.current.zKey.isPressed)
            bucketInput = 1f;

        if (Keyboard.current.xKey.isPressed)
            bucketInput = -1f;

        // Apply boom movement
        if (mainBoom != null && boomInput != 0f)
        {
            boomAngle += boomInput * boomSpeed * Time.deltaTime;
            boomAngle = Mathf.Clamp(boomAngle, boomMin, boomMax);

            Vector3 rotation = mainBoom.localEulerAngles;
            rotation.x = boomAngle;
            mainBoom.localEulerAngles = rotation;
        }

        // Apply arm movement
        if (arm != null && armInput != 0f)
        {
            armAngle += armInput * armSpeed * Time.deltaTime;
            armAngle = Mathf.Clamp(armAngle, armMin, armMax);

            Vector3 rotation = arm.localEulerAngles;
            rotation.x = armAngle;
            arm.localEulerAngles = rotation;
        }

        // Apply bucket movement
        if (bucket != null && bucketInput != 0f)
        {
            bucketAngle += bucketInput * bucketSpeed * Time.deltaTime;
            bucketAngle = Mathf.Clamp(bucketAngle, bucketMin, bucketMax);

            Vector3 rotation = bucket.localEulerAngles;
            rotation.x = bucketAngle;
            bucket.localEulerAngles = rotation;
        }
    }
}