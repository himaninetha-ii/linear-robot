# LinearRobot-Planner
Runs Behavior Tree to perform a pick or place action

flowchart TD
    
    Root --> Main
    Main --> PreAction
    Main --> ActionSeq
    Main --> PostAction

    PreAction --> IntermediateSeq
    IntermediateSeq --> ComputeIntermediate
    IntermediateSeq --> GoToIntermediate
    PreAction --> GoToPreAction

    ActionSeq --> PickOrPlace
    ActionSeq --> GripperAction

    PickOrPlace --> PickSelector
    PickSelector --> InvertPick
    PickSelector --> PickSequence
    PickSequence --> PickType
    PickType --> InvertVision
    PickType --> VisionPickSeq
    VisionPickSeq --> VisionPick
    VisionPickSeq --> GoToVisionIntermediate
    PickSequence --> GoToPick

    PickOrPlace --> PlaceSelector
    PlaceSelector --> InvertPlace
    PlaceSelector --> PlaceSeq
    PlaceSeq --> PlaceType
    PlaceType --> InvertAccPlace
    PlaceType --> AccuratePlace
    AccuratePlace --> GoToAccurateOffset
    AccuratePlace --> GoToAccurateDown
    AccuratePlace --> GoToAccurateCorrection
    PlaceSeq --> GoToPlace

    PostAction --> GoToPostAction
