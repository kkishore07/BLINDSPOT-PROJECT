using UnityEngine;

public class WorkerMovement : MonoBehaviour
{
    public Transform target;
    public float walkingSpeed = 1.5f;

    void Update()
    {
        if (target == null)
            return;

        Vector3 direction = target.position - transform.position;
        direction.y = 0;

        if (direction.magnitude > 1.5f)
        {
            transform.position += direction.normalized * walkingSpeed * Time.deltaTime;

            transform.rotation = Quaternion.LookRotation(direction);
        }
    }
}