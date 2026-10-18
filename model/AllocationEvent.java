package model;
import java.time.LocalDateTime;
public class AllocationEvent {
    private final int eventId; private final String eventType,description; private final LocalDateTime timestamp;
    public AllocationEvent(int eventId,String eventType,String description){this.eventId=eventId;this.eventType=eventType;this.description=description;this.timestamp=LocalDateTime.now();}
    public int getEventId(){return eventId;} public String getEventType(){return eventType;} public String getDescription(){return description;} public LocalDateTime getTimestamp(){return timestamp;}
    public String toString(){return "["+timestamp+"] "+eventType+" : "+description;}
}
