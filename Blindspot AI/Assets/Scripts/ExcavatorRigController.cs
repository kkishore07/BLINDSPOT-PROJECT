using UnityEngine;
using UnityEngine.InputSystem;

public class ExcavatorRigController : MonoBehaviour
{
    [Header("Rig Bones")]
    public Transform boomBone;
    public Transform armBone;
    public Transform bucketBone;

    [Header("Normal Speeds")]
    public float boomSpeed = 25f;
    public float armSpeed = 30f;
    public float bucketSpeed = 35f;

    [Header("Safety Control")]
    public float safetySpeedMultiplier = 1f;
    public bool emergencyStop = false;

    private Quaternion boomStartRotation;
    private Quaternion armStartRotation;
    private Quaternion bucketStartRotation;

    private float boomAngle;
    private float armAngle;
    private float bucketAngle;

    void Start()
    {
        if (boomBone != null)
        {
            boomStartRotation = boomBone.localRotation;
            boomAngle = 0f;
        }

        if (armBone != null)
        {
            armStartRotation = armBone.localRotation;
            armAngle = 0f;
        }

        if (bucketBone != null)
        {
            bucketStartRotation = bucketBone.localRotation;
            bucketAngle = 0f;
        }
    }

    void Update()
    {
        if (Keyboard.current == null)
            return;

        // CRITICAL SAFETY STOP
        // No driving or arm movement is allowed.
        if (emergencyStop)
            return;

        float speedMultiplier = safetySpeedMultiplier;

        // -------------------------
        // BOOM - Q / E
        // -------------------------

        float boomInput = 0f;

        if (Keyboard.current.qKey.isPressed)
            boomInput = 1f;

        if (Keyboard.current.eKey.isPressed)
            boomInput = -1f;

        // -------------------------
        // ARM - R / F
        // -------------------------

        float armInput = 0f;

        if (Keyboard.current.rKey.isPressed)
            armInput = 1f;

        if (Keyboard.current.fKey.isPressed)
            armInput = -1f;

        // -------------------------
        // BUCKET - Z / X
        // -------------------------

        float bucketInput = 0f;

        if (Keyboard.current.zKey.isPressed)
            bucketInput = 1f;

        if (Keyboard.current.xKey.isPressed)
            bucketInput = -1f;

        // -------------------------
        // BOOM
        // -------------------------

        if (boomBone != null && boomInput != 0f)
        {
            boomAngle +=
                boomInput *
                boomSpeed *
                speedMultiplier *
                Time.deltaTime;

            boomBone.localRotation =
                boomStartRotation *
                Quaternion.Euler(boomAngle, 0f, 0f);
        }

        // -------------------------
        // ARM
        // -------------------------

        if (armBone != null && armInput != 0f)
        {
            armAngle +=
                armInput *
                armSpeed *
                speedMultiplier *
                Time.deltaTime;

            armBone.localRotation =
                armStartRotation *
                Quaternion.Euler(armAngle, 0f, 0f);
        }

        // -------------------------
        // BUCKET
        // -------------------------

        if (bucketBone != null && bucketInput != 0f)
        {
            bucketAngle +=
                bucketInput *
                bucketSpeed *
                speedMultiplier *
                Time.deltaTime;

            bucketBone.localRotation =
                bucketStartRotation *
                Quaternion.Euler(bucketAngle, 0f, 0f);
        }
    }
}