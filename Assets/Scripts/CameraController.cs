using UnityEngine;

public class CameraController : MonoBehaviour
{
    [Header("Rotation Settings")]
    [Tooltip("마우스 움직임에 따른 최대 회전 각도")]
    public float maxRotationAngle = 5f;
    
    [Tooltip("회전 부드러움 (값이 클수록 빠르게 반응)")]
    public float smoothSpeed = 5f;
    
    [Header("Optional Settings")]
    [Tooltip("X축(좌우) 회전 활성화")]
    public bool enableXRotation = true;
    
    [Tooltip("Y축(상하) 회전 활성화")]
    public bool enableYRotation = true;
    
    private Quaternion initialRotation;
    private Quaternion targetRotation;
    
    void Start()
    {
        // 초기 회전값 저장
        initialRotation = transform.rotation;
        targetRotation = initialRotation;
    }
    
    void Update()
    {
        // 마우스 위치를 화면 중심 기준 -1 ~ 1 범위로 정규화
        Vector2 mousePosition = Input.mousePosition;
        float normalizedX = (mousePosition.x / Screen.width) * 2f - 1f;
        float normalizedY = (mousePosition.y / Screen.height) * 2f - 1f;
        
        // 회전 각도 계산
        float rotationX = enableYRotation ? -normalizedY * maxRotationAngle : 0f;
        float rotationY = enableXRotation ? normalizedX * maxRotationAngle : 0f;
        
        // 목표 회전값 설정
        targetRotation = initialRotation * Quaternion.Euler(rotationX, rotationY, 0f);
        
        // 부드럽게 회전
        transform.rotation = Quaternion.Slerp(transform.rotation, targetRotation, smoothSpeed * Time.deltaTime);
    }
    
    /// <summary>
    /// 초기 회전값을 현재 회전값으로 재설정
    /// </summary>
    public void ResetInitialRotation()
    {
        initialRotation = transform.rotation;
    }
}
