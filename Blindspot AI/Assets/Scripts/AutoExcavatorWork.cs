using UnityEngine;

public class AutoExcavatorWork : MonoBehaviour
{
    [Header("Rig Bones")]
    public Transform boomBone;
    public Transform armBone;
    public Transform bucketBone;

    [Header("Normal Speeds")]
    public float boomSpeed = 15f;
    public float armSpeed = 20f;
    public float bucketSpeed = 25f;

    [Header("Automatic Mode")]
    public bool automaticWork = true;

    [Header("Safety System")]
    public bool emergencyStop = false;
    public float safetySpeedMultiplier = 1f;

    private Quaternion boomStart;
    private Quaternion armStart;
    private Quaternion bucketStart;

    private float timer = 0f;

    void Start()
    {
        if (boomBone != null)
            boomStart = boomBone.localRotation;

        if (armBone != null)
            armStart = armBone.localRotation;

        if (bucketBone != null)
            bucketStart = bucketBone.localRotation;
    }

    void Update()
    {
        if (!automaticWork)
            return;

        // CRITICAL SAFETY STOP
        if (emergencyStop)
            return;

        timer += Time.deltaTime;

        float cycle = timer % 12f;

        if (cycle < 3f)
        {
            // LOWER BOOM
            RotateBone(
                boomBone,
                boomStart,
                -20f,
                boomSpeed * safetySpeedMultiplier
            );
        }
        else if (cycle < 6f)
        {
            // MOVE ARM
            RotateBone(
                armBone,
                armStart,
                25f,
                armSpeed * safetySpeedMultiplier
            );
        }
        else if (cycle < 8f)
        {
            // CURL BUCKET
            RotateBone(
                bucketBone,
                bucketStart,
                35f,
                bucketSpeed * safetySpeedMultiplier
            );
        }
        else if (cycle < 10f)
        {
            // LIFT BOOM
            RotateBone(
                boomBone,
                boomStart,
                10f,
                boomSpeed * safetySpeedMultiplier
            );
        }
        else
        {
            // DUMP BUCKET
            RotateBone(
                bucketBone,
                bucketStart,
                -20f,
                bucketSpeed * safetySpeedMultiplier
            );
        }
    }

    void RotateBone(
        Transform bone,
        Quaternion startRotation,
        float targetAngle,
        float speed)
    {
        if (bone == null)
            return;

        Quaternion target =
            startRotation *
            Quaternion.Euler(targetAngle, 0f, 0f);

        bone.localRotation =
            Quaternion.RotateTowards(
                bone.localRotation,
                target,
                speed * Time.deltaTime
            );
    }
}